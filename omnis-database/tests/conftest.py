"""
Fixtures of the warehouse's tests, which test the SQL of omnis-database/init/ on a throwaway Postgres
(the image of the stack), through psycopg2 directly. They don't depend on the omnis package.
"""
from uuid import uuid4

import pytest

from warehouse_helper import ENGINE, LOGINS, SUPERUSER, Server, Warehouse

POSTGRES_IMAGE = "postgres:16"

# The tests that use the fixtures below are marked `integration` in their module (pytestmark)


@pytest.fixture(scope="session")
def server() -> Server:
    """
    A throwaway Postgres for the whole session. Roles belong to the whole server, not to a database,
    so they are created once: the engine's, the groups (by the init, on the admin database) and a
    login of each group.
    """
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer(POSTGRES_IMAGE, driver=None) as container:
        server = Server(
            host=container.get_container_host_ip(),
            port=int(container.get_exposed_port(5432)),
            superuser=container.username,
            password=container.password,
            database=container.dbname,
        )
        admin = Warehouse(server, server.database)
        admin.execute(SUPERUSER, f"CREATE ROLE {ENGINE} LOGIN PASSWORD '{ENGINE}'")
        admin.apply_init()
        for login, group in LOGINS.items():
            admin.execute(SUPERUSER, f"CREATE ROLE {login} LOGIN PASSWORD '{login}' IN ROLE {group}")
        yield server


@pytest.fixture
def database(server) -> Warehouse:
    """An empty database of its own for one test, without the init applied."""
    name = f"test_{uuid4().hex[:12]}"
    admin = server.connect(server.database)
    admin.autocommit = True
    try:
        admin.cursor().execute(f'CREATE DATABASE "{name}"')
        yield Warehouse(server, name)
        admin.cursor().execute(f'DROP DATABASE "{name}" WITH (FORCE)')
    finally:
        admin.close()


@pytest.fixture
def warehouse(database) -> Warehouse:
    """A database of its own for one test, with the init applied, as omnis-database-init leaves it."""
    database.apply_init()
    return database
