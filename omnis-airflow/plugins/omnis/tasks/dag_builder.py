from typing import assert_never

from airflow.sdk import DAG, task

from omnis.domain import Etl, Flow, Node, Pipe, RawLoad
from omnis.ports import DataSource, EtlExecutor

CREATE_TABLES_TASK_ID = "create_tables"


class DAGBuilder:
    """
    Turns a Flow into an Airflow DAG: a first task that creates the flow's tables, then one task
    per node of its graph, wired as the graph says.

    Tasks run on the ports given here. Airflow parses the DAG file again to run each task, so
    they are closures over what the DAG file injected, not lookups by name.
    """

    def __init__(self, flow: Flow, executor: EtlExecutor, raw_files: DataSource):
        if CREATE_TABLES_TASK_ID in {node.name for node in flow.nodes}:
            raise ValueError(f"Flow '{flow.name}': '{CREATE_TABLES_TASK_ID}' is reserved and cannot be a node name")
        self._flow = flow
        self._executor = executor
        self._raw_files = raw_files

    def build_airflow_dag(self, *, tags: list[str] | None = None, **dag_arguments) -> DAG:
        """
        The DAG id is the flow name. Any other DAG argument (schedule, default_args...) is passed
        through to Airflow.
        """
        flow = self._flow
        dag_arguments.setdefault("catchup", False)
        with DAG(
            dag_id=flow.name,
            tags=["omnis", *(tags or [])],
            doc_md=f"Flow `{flow.name}`, built from `dags/{flow.name}/`.",
            **dag_arguments,
        ) as dag:
            tables = self._create_tables_task()

            tasks = {node.name: self._task_for(node) for node in flow.nodes}
            for node in flow.nodes:
                upstream = flow.upstream(node.name)
                for upstream_name in upstream:
                    tasks[upstream_name] >> tasks[node.name]  # pyright: ignore[reportUnusedExpression]
                if not upstream:
                    tables >> tasks[node.name]  # pyright: ignore[reportUnusedExpression]

        return dag

    def _task_for(self, node: Node):
        match node:
            case Etl():
                return self._etl_task(node, self._flow.pipe_of(node))
            case RawLoad():
                return self._raw_load_task(node)
            case _:
                assert_never(node)

    def _create_tables_task(self):
        tables = self._flow.tables

        @task(task_id=CREATE_TABLES_TASK_ID)
        def create_tables():
            """Apply the DDL of every table of the flow. Tables that already exist are left as they are."""
            self._executor.create_tables(tables)

        return create_tables()

    def _etl_task(self, etl: Etl, pipe: Pipe):
        doc = (
            f"ETL into `{etl.destination}` ({etl.strategy.value}"
            + (f", key {', '.join(etl.key)}" if etl.key else "")
            + f") with pipe `{pipe.name}`:\n\n```sql\n{pipe.query}\n```"
        )

        @task(task_id=etl.name, doc_md=doc)
        def run_etl():
            """Write the rows of the pipe into the ETL's destination. Returns the rows written."""
            return self._executor.run(etl, pipe)

        return run_etl()

    def _raw_load_task(self, raw_load: RawLoad):
        doc = f"Raw load of the files under `{raw_load.source}` into `{raw_load.destination}`."

        @task(task_id=raw_load.name, doc_md=doc)
        def load_raw():
            """Replace the landing table with every file under the source. Returns the rows loaded."""
            source = self._raw_files
            files = ((path, source.read(path)) for path in source.list_files(raw_load.source))
            return self._executor.load_raw(raw_load, files)

        return load_raw()
