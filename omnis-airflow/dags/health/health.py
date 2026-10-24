"""
Airflow DAG of the health flow: gym series and running sessions.

This file is the flow's entry point, so it builds the dependencies the flow runs with.
What runs and in which order is in graph.yaml, tasks/, tables/ and artifacts/ next to this file.
"""
from pathlib import Path

from omnis.adapters import (
    ArchiveTaskType,
    EmailNotifier,
    EtlTaskType,
    LocalDataSource,
    PostgresDatabase,
    RawLoadTaskType,
    S3DataSource,
    SqlArchiveRunner,
    SqlDdlRunner,
    SqlEtlRunner,
    SqlPipeParser,
    SqlRawLoadRunner,
    SqlTableParser,
    TaskParser,
    YamlParser,
    YamlTaskDependenciesParser,
)
from omnis.config_helper import load_environment_config
from omnis.domain import Flow
from omnis.ports import PipeRepository, TableRepository, TaskDependenciesRepository, TaskRepository

env = load_environment_config()

artifacts = LocalDataSource(Path(__file__).parent)
raw_files = S3DataSource(**env.storage_config.model_dump(), bucket=env.data_bucket_name)
warehouse = PostgresDatabase(env.db_conn)
notifier = EmailNotifier(**env.email.model_dump()) if env.email is not None else None

flow = Flow(
    "health",
    task_dependencies_repository=TaskDependenciesRepository(artifacts, YamlTaskDependenciesParser()),
    # The types of task this flow declares, and where each one runs
    task_repository=TaskRepository(artifacts, TaskParser(YamlParser(), task_types=[
        EtlTaskType(pipe_repository=PipeRepository(artifacts, SqlPipeParser()), runner=SqlEtlRunner(warehouse)),
        RawLoadTaskType(runner=SqlRawLoadRunner(warehouse, raw_files=raw_files)),
        ArchiveTaskType(runner=SqlArchiveRunner(warehouse, raw_files=raw_files)),
    ])),
    table_repository=TableRepository(artifacts, SqlTableParser()),
    ddl_runner=SqlDdlRunner(warehouse),
    notifier=notifier,
)

dag = flow.build_airflow_dag(
    schedule="0 * * * *",
    # Two runs at once would share the raw tables: one run's raw load could replace them while the other processes them
    max_active_runs=1,
    # A failed run pauses the DAG, so no more runs start until someone looks at it and unpauses it
    max_consecutive_failed_dag_runs=1,
    tags=["health"],
)
