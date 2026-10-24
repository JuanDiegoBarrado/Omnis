from uuid import uuid4

import boto3
import psycopg2
import pytest

from omnis.tests.postgres_helper import PostgresHelper

# The same images as the stack, so the adapters are tested against what they run on
POSTGRES_IMAGE = "postgres:16"
MINIO_IMAGE = "quay.io/minio/minio:latest"

# The tests that use the fixtures below are marked `integration` in their module (pytestmark)


@pytest.fixture(scope="session")
def postgres_server() -> str:
    """A throwaway Postgres for the whole session: the DSN of its admin database."""
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer(POSTGRES_IMAGE, driver=None) as container:
        yield container.get_connection_url()


@pytest.fixture
def postgres(postgres_server) -> PostgresHelper:
    """An empty database of its own for one test."""
    name = f"test_{uuid4().hex[:12]}"
    admin = psycopg2.connect(postgres_server)
    admin.autocommit = True
    try:
        admin.cursor().execute(f'CREATE DATABASE "{name}"')
        yield PostgresHelper(f"{postgres_server.rsplit('/', 1)[0]}/{name}")
        admin.cursor().execute(f'DROP DATABASE "{name}" WITH (FORCE)')
    finally:
        admin.close()


@pytest.fixture(scope="session")
def minio_server() -> dict:
    """A throwaway MinIO for the whole session: the arguments of an S3 client for it."""
    from testcontainers.minio import MinioContainer

    with MinioContainer(MINIO_IMAGE) as container:
        config = container.get_config()
        yield {
            "service_name": "s3",
            "endpoint_url": f"http://{config['endpoint']}",
            "aws_access_key_id": config["access_key"],
            "aws_secret_access_key": config["secret_key"],
        }


@pytest.fixture
def s3_bucket(minio_server) -> tuple[dict, str]:
    """An empty bucket of its own for one test: the client arguments and the bucket name."""
    bucket = f"test-{uuid4().hex[:12]}"
    boto3.client(**minio_server).create_bucket(Bucket=bucket)
    return minio_server, bucket
