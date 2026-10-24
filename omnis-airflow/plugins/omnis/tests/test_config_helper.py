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

# Optional: without all of them but SMTP_PORT, nobody is notified
EMAIL_ENVIRONMENT = {
    "ALERT_EMAIL": "alerts@example.com",
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": "465",
    "SMTP_USER": "omnis@gmail.com",
    "SMTP_PASSWORD": "app password",
}


@pytest.fixture
def environment(monkeypatch):
    for name, value in ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    for name in EMAIL_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)
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


def test_builds_the_email_config_when_every_variable_is_set(environment):
    """
    Checks: with ALERT_EMAIL and every SMTP_* variable set, the config has the e-mail settings:
    the SMTP server, its port as a number, the account and the recipient.

    If it fails: a complete .env would not turn the failure e-mails on, or they would go through the
    wrong server or to the wrong address.
    """
    for name, value in EMAIL_ENVIRONMENT.items():
        environment.setenv(name, value)

    email = load_environment_config().email

    assert email is not None
    assert email.model_dump() == {
        "host": "smtp.gmail.com", "port": 465, "user": "omnis@gmail.com", "password": "app password", "to": "alerts@example.com",
    }


def test_the_smtp_port_is_587_unless_set(environment):
    """
    Checks: without SMTP_PORT (or with it empty), the e-mails go through port 587, the usual
    STARTTLS one.

    If it fails: a .env that leaves SMTP_PORT out would turn the e-mails off, or crash the DAG files.
    """
    for name, value in EMAIL_ENVIRONMENT.items():
        environment.setenv(name, value)
    environment.setenv("SMTP_PORT", "")

    assert load_environment_config().email.port == 587


@pytest.mark.parametrize("name", ["ALERT_EMAIL", "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"])
def test_without_any_email_variable_nobody_is_notified(environment, name):
    """
    Checks: if any variable an e-mail needs is missing (the test id says which), the config has no
    e-mail settings, and loading it doesn't fail: the flows run without notifier.

    If it fails: an incomplete .env would break every DAG file, or build a notifier that fails on
    every failed run instead of leaving the e-mails off.
    """
    for other, value in EMAIL_ENVIRONMENT.items():
        environment.setenv(other, value)
    environment.delenv(name)

    assert load_environment_config().email is None
