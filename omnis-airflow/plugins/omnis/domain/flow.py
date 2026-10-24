from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from airflow.sdk import DAG

from omnis.domain.tasks import DDL, Task

if TYPE_CHECKING:
    from omnis.ports import (
        TableRepository,
        TaskDependenciesRepository,
        TaskRepository,
        TaskRunner,
    )

class Flow:
    """
    A data flow, built from its artifacts: the graph that says which task precedes which, its
    tasks (each ETL with its pipe) and its tables.

    A repository per kind of artifact of this flow is injected (the tasks come with the runner
    each runs on), and the runner of its DDL task. On creation it checks that the graph and the
    repository name the same tasks, that each table has a single writer, and that each table is
    created once: by its DDL, or by the task that writes it (see Task.creates).
    """

    def __init__(self,
        name:                           str,
        task_dependencies_repository:   TaskDependenciesRepository,
        task_repository:                TaskRepository,
        table_repository:               TableRepository,
        ddl_runner:                     TaskRunner[DDL]
    ):
        self.name = name
        self.task_dependencies_repository = task_dependencies_repository
        self.task_repository = task_repository
        self.table_repository = table_repository
        self.ddl_runner = ddl_runner

        # Load dependencies between tasks
        task_dependencies = task_dependencies_repository.find()
        if task_dependencies is None:
            raise LookupError(f"Flow '{name}' has no task dependencies")
        self.task_dependencies = task_dependencies

        # Load the tasks of the flow: check their names against the graph before building them
        task_names = set(task_repository.query_names())

        undefined = sorted(set(task_dependencies.tasks) - task_names)
        if undefined:
            raise ValueError(f"Flow '{name}': tasks of the graph without definition {undefined}")

        unused = sorted(task_names - set(task_dependencies.tasks))
        if unused:
            raise ValueError(f"Flow '{name}': tasks not in the graph {unused}")

        if DDL.NAME in task_names:
            raise ValueError(f"Flow '{name}': '{DDL.NAME}' is reserved and cannot be a task name")

        self.tasks: list[Task] = task_repository.find_all(task_dependencies.tasks)

        # TODO what is this?
        writers = Counter(table for task in self.tasks for table in task.writes)
        shared = sorted(table for table, count in writers.items() if count > 1)
        if shared:
            raise ValueError(f"Flow '{name}': tables written by more than one task {shared}")

        # Load tables of the database
        self.tables = table_repository.find_all(table_repository.query_names())

        # Each table is created once: by its DDL, or by the task that writes it
        with_ddl = {table.name for table in self.tables}
        for task in self.tasks:
            without_ddl = sorted(set(task.writes) - set(task.creates) - with_ddl)
            if without_ddl:
                raise ValueError(f"Flow '{name}': task '{task.name}' writes tables without DDL {without_ddl}")
            created_twice = sorted(set(task.creates) & with_ddl)
            if created_twice:
                raise ValueError(f"Flow '{name}': task '{task.name}' creates tables itself, so they must not have DDL {created_twice}")

        self.ddl = DDL(tables=tuple(self.tables), runner=ddl_runner)

    def build_airflow_dag(self, *, tags: list[str] | None = None, **dag_arguments) -> DAG:
        """
        The Airflow DAG of the flow: its DDL task first, then a task per node of the graph, wired
        as the graph says. The DAG id is the flow name; any other DAG argument (schedule,
        default_args...) is passed through to Airflow.

        Airflow parses the DAG file again to run each task, so every task runs on the runner
        that file injected for it.
        """
        # TODO what is this?
        dag_arguments.setdefault("catchup", False)
        
        with DAG(
            dag_id=self.name,
            tags=["omnis", *(tags or [])],
            doc_md=f"Flow `{self.name}`.",
            **dag_arguments,
        ) as dag:
            ddl_task = self.ddl.build_task()
            tasks = {task.name: task.build_task() for task in self.tasks}
            for task in self.tasks:
                preceding = self.task_dependencies.preceding_tasks(task.name)
                for preceding_name in preceding:
                    tasks[preceding_name] >> tasks[task.name]  # pyright: ignore[reportUnusedExpression]
                if not preceding:
                    ddl_task >> tasks[task.name]  # pyright: ignore[reportUnusedExpression]

        return dag
