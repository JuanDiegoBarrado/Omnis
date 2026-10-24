import logging
import os
from urllib.parse import quote_plus

from omnis.schemas.config import EmailConfig, EnvironmentConfig, StorageConfig

logger = logging.getLogger(__name__)

# What a failure e-mail needs. SMTP_PORT is optional (587 by default)
_EMAIL_VARIABLES = ('ALERT_EMAIL', 'SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD')


def _require(name: str) -> str:
    """Return the value of an environment variable, failing fast if it is unset."""
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Required environment variable '{name}' is not set")
    return value


def _email_config() -> EmailConfig | None:
    """The failure e-mail settings, or None unless every one of _EMAIL_VARIABLES is set."""
    missing = [name for name in _EMAIL_VARIABLES if not os.getenv(name)]
    if missing:
        if len(missing) < len(_EMAIL_VARIABLES):
            logger.warning(f"Failure e-mails are off: {missing} not set")
        return None
    return EmailConfig(
        host=os.environ['SMTP_HOST'],
        port=int(os.getenv('SMTP_PORT') or 587),
        user=os.environ['SMTP_USER'],
        password=os.environ['SMTP_PASSWORD'],
        to=os.environ['ALERT_EMAIL'],
    )


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
        email=_email_config(),
    )
