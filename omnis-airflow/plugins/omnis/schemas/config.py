from pydantic import BaseModel


class StorageConfig(BaseModel):
    """S3/MinIO client configuration (kwargs for the storage adapter)."""

    service_name: str
    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str


class EnvironmentConfig(BaseModel):
    """Runtime configuration resolved from environment variables."""

    db_conn: str
    storage_config: StorageConfig
    data_bucket_name: str
