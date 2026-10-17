"""
Catalog of ready-made implementations of the ports.

Each flow's DAG file (dags/<flow>/<flow>.py) is its entry point: it picks from here the
dependencies it runs with and injects them into a DAGBuilder. Nothing else builds adapters.
"""
from pathlib import Path

from omnis.adapters import (
    LocalDataSource,
    PostgresDatabase,
    S3DataSource,
    SqlEtlExecutor,
    SqlPipeParser,
    SqlTableParser,
    YamlEtlGraphParser,
    YamlEtlParser,
)
from omnis.config_helper import load_environment_config
from omnis.domain import EtlGraph, Flow
from omnis.ports import DataSource, EtlExecutor, EtlGraphRepository, EtlRepository, PipeRepository, TableRepository

# Each flow is a folder of the DAGs folder (a sibling of plugins/): <flow>/graph.yaml, <flow>/etls/,
# <flow>/pipes/ and <flow>/tables/
ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "dags"
GRAPH_FILE_NAME = "graph"


def get_artifact_source() -> DataSource:
    return LocalDataSource(ARTIFACTS_DIR)


def get_etl_repository(flow: str) -> EtlRepository:
    return EtlRepository(get_artifact_source(), YamlEtlParser(), f"{flow}/etls")


def get_pipe_repository(flow: str) -> PipeRepository:
    return PipeRepository(get_artifact_source(), SqlPipeParser(), f"{flow}/pipes")


def get_table_repository(flow: str) -> TableRepository:
    return TableRepository(get_artifact_source(), SqlTableParser(), f"{flow}/tables")


def get_etl_graph_repository(flow: str) -> EtlGraphRepository:
    return EtlGraphRepository(get_artifact_source(), YamlEtlGraphParser(flow, get_etl_repository(flow)), flow)


def get_etl_graph(flow: str) -> EtlGraph:
    """The graph of `flow` (<flow>/graph.yaml)."""
    graph = get_etl_graph_repository(flow).find(GRAPH_FILE_NAME)
    if graph is None:
        raise LookupError(f"Flow '{flow}' has no graph: expected {ARTIFACTS_DIR / flow / GRAPH_FILE_NAME}.yaml")
    return graph


def load_flow(flow: str) -> Flow:
    """The flow defined in dags/<flow>/: its graph, pipes and tables."""
    return Flow(
        get_etl_graph(flow),
        get_pipe_repository(flow).find_all(),
        get_table_repository(flow).find_all(),
    )


def postgres_etl_executor() -> EtlExecutor:
    """Runs flows against the Omnis database (POSTGRES_* env vars)."""
    env = load_environment_config()
    return SqlEtlExecutor(PostgresDatabase(env.db_conn))


def minio_raw_files() -> DataSource:
    """The data bucket of MinIO (MINIO_* env vars), where producers drop the raw files."""
    env = load_environment_config()
    return S3DataSource(**env.storage_config.model_dump(), bucket=env.data_bucket_name)
