import pytest

from omnis.adapters import LocalDataSource
from omnis.domain import Etl, EtlGraph, Flow, Pipe, RawLoad, Table
from omnis.ports import EtlExecutor
from omnis.tasks import DAGBuilder


class FakeExecutor(EtlExecutor):
    """Records what each task asks for instead of touching a database."""

    def __init__(self):
        self.calls = []

    def create_tables(self, tables):
        self.calls.append(("create_tables", [table.name for table in tables]))

    def load_raw(self, raw_load, files):
        self.calls.append(("load_raw", raw_load.name, [path for path, _ in files]))
        return 1

    def run(self, etl, pipe):
        self.calls.append(("run", etl.name, pipe.name))
        return 2


def flow():
    graph = EtlGraph(
        "health",
        [
            RawLoad(name="raw.x", source="raw/new/x/", destination="raw.x", columns=("a",)),
            Etl(name="orig.x", destination="orig.x", pipe="orig.x"),
        ],
        {"orig.x": ["raw.x"]},
    )
    return Flow(graph, [Pipe(name="orig.x", query="SELECT a FROM raw.x")], [Table(name="orig.x", ddl="...")])


@pytest.fixture
def raw_files(tmp_path):
    (tmp_path / "raw/new/x").mkdir(parents=True)
    (tmp_path / "raw/new/x/x_1.csv").write_bytes(b"a\n1\n")
    return LocalDataSource(tmp_path)


def test_builds_one_task_per_node_after_create_tables(raw_files):
    dag = DAGBuilder(flow(), FakeExecutor(), raw_files).build_airflow_dag(schedule=None, tags=["health"])

    assert dag.dag_id == "health"
    assert set(dag.task_dict) == {"create_tables", "raw.x", "orig.x"}
    assert dag.get_task("raw.x").upstream_task_ids == {"create_tables"}
    assert dag.get_task("orig.x").upstream_task_ids == {"raw.x"}
    assert "omnis" in dag.tags and "health" in dag.tags


def test_tasks_run_on_the_injected_ports(raw_files):
    executor = FakeExecutor()
    dag = DAGBuilder(flow(), executor, raw_files).build_airflow_dag(schedule=None)

    for task_id in ("create_tables", "raw.x", "orig.x"):
        dag.get_task(task_id).python_callable()

    assert executor.calls == [
        ("create_tables", ["orig.x"]),
        ("load_raw", "raw.x", ["raw/new/x/x_1.csv"]),
        ("run", "orig.x", "orig.x"),
    ]


def test_rejects_a_node_named_like_the_create_tables_task(raw_files):
    graph = EtlGraph("health", [Etl(name="create_tables", destination="orig.x", pipe="p")], {})
    reserved = Flow(graph, [Pipe(name="p", query="SELECT 1")], [Table(name="orig.x", ddl="...")])

    with pytest.raises(ValueError, match="reserved"):
        DAGBuilder(reserved, FakeExecutor(), raw_files)
