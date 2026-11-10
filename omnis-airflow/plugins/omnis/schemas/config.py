from pydantic import BaseModel


class EmailConfig(BaseModel):
    """Who gets the failure e-mails, and the SMTP server they are sent through (kwargs for EmailNotifier)."""

    host: str
    port: int
    user: str
    password: str
    to: str


class EnvironmentConfig(BaseModel):
    """Runtime configuration resolved from environment variables."""

    db_conn: str
    # The landing zone of omnis-storage as Airflow sees it: raw/new/<entity>/ and raw/his/<entity>/
    storage_data_dir: str
    # None when the environment doesn't give everything an e-mail needs: then nobody is notified
    email: EmailConfig | None = None
