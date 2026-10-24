import pytest

from omnis.config_helper import load_environment_config

ENVIRONMENT = {
    "POSTGRES_USER": "omnis",
    "POSTGRES_PASSWORD": "p@ss:/word",
    "POSTGRES_HOST": "omnis-database",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "warehouse",
    "MINIO_ENDPOINT": "omnis-storage:9000",
    "MINIO_ROOT_USER": "minio",
    "MINIO_ROOT_PASSWORD": "secret",
    "MINIO_DATA_BUCKET": "data",
}


@pytest.fixture
def environment(monkeypatch):
    for name, value in ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    return monkeypatch


def test_builds_the_config_from_the_environment(environment):
    """
    Checks: the env vars the compose passes to Airflow become the Postgres connection string, the
    S3 client settings and the data bucket. A password with URL characters (@ : /) is escaped.

    If it fails: the DAGs would connect to the wrong database or bucket, or fail to connect at all
    when the password has special characters.
    """
    config = load_environment_config()

    assert config.db_conn == "postgresql://omnis:p%40ss%3A%2Fword@omnis-database:5432/warehouse"
    assert config.storage_config.endpoint_url == "http://omnis-storage:9000"
    assert config.storage_config.aws_access_key_id == "minio"
    assert config.storage_config.aws_secret_access_key == "secret"
    assert config.data_bucket_name == "data"


@pytest.mark.parametrize("name", sorted(ENVIRONMENT))
def test_a_missing_variable_fails_fast(environment, name):
    """
    Checks: each required env var, if missing, makes loading the config fail with an error that
    names it (the test id says which variable).

    If it fails: a variable missing from the compose would go unnoticed when the DAG file is parsed,
    and the tasks would fail later connecting to "None", without saying which variable is missing.
    """
    environment.delenv(name)

    with pytest.raises(EnvironmentError, match=name):
        load_environment_config()
