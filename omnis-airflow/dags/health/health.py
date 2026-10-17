"""
Airflow DAG of the health flow: gym series and running sessions.

This file is the flow's entry point, so it declares the dependencies the flow runs with.
What runs and in which order is in graph.yaml, etls/, pipes/ and tables/ next to this file.
"""
from omnis import container
from omnis.tasks import DAGBuilder

builder = DAGBuilder(
    flow=container.load_flow("health"),
    executor=container.postgres_etl_executor(),
    raw_files=container.minio_raw_files(),
)

dag = builder.build_airflow_dag(
    schedule="0 23 * * *",
    tags=["health"],
)
