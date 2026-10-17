import os
from urllib.parse import quote_plus

from omnis.schemas.config import EnvironmentConfig, StorageConfig


def _require(name: str) -> str:
    """Return the value of an environment variable, failing fast if it is unset."""
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Required environment variable '{name}' is not set")
    return value


def load_environment_config() -> EnvironmentConfig:
    database_user = quote_plus(_require('POSTGRES_USER'))
    database_password = quote_plus(_require('POSTGRES_PASSWORD'))

    return EnvironmentConfig(
        db_conn=(
            f"postgresql://{database_user}:{database_password}"
            f"@{_require('POSTGRES_HOST')}:{_require('POSTGRES_PORT')}/{_require('POSTGRES_DB')}"
        ),
        storage_config=StorageConfig(
            service_name='s3',
            endpoint_url=f"http://{_require('MINIO_ENDPOINT')}",
            aws_access_key_id=_require('MINIO_ROOT_USER'),
            aws_secret_access_key=_require('MINIO_ROOT_PASSWORD'),
        ),
        data_bucket_name=_require('MINIO_DATA_BUCKET'),
    )
