from uuid import uuid4

import boto3
import psycopg2
import pytest

from omnis.tests.postgres_helper import PostgresHelper

# The same image as the stack, so the adapters are tested against what they run on
POSTGRES_IMAGE = "postgres:16"

# The tests that use the Postgres fixtures below are marked `integration` in their module (pytestmark)


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
def s3_server() -> dict:
    """
    A throwaway S3 for the whole session, served over HTTP in this process by moto: the arguments of
    an S3 client for it. The stack has no S3 (its landing zone is a folder), so S3DataSource is
    tested against moto rather than a container of a server that could stop being published.
    """
    from moto.server import ThreadedMotoServer

    server = ThreadedMotoServer(ip_address="127.0.0.1", port=0)
    server.start()
    host, port = server.get_host_and_port()
    yield {
        "service_name": "s3",
        "endpoint_url": f"http://{host}:{port}",
        "aws_access_key_id": "testing",
        "aws_secret_access_key": "testing",
    }
    server.stop()


@pytest.fixture
def s3_bucket(s3_server) -> tuple[dict, str]:
    """An empty bucket of its own for one test: the client arguments and the bucket name."""
    bucket = f"test-{uuid4().hex[:12]}"
    boto3.client(**s3_server).create_bucket(Bucket=bucket)
    return s3_server, bucket
