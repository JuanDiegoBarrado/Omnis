"""
What each role of the warehouse can do with the tables of a flow: the engine (omnis_airflow), and a
login of each group (database_admin, database_user, visualization).
"""
import pytest
from psycopg2 import errors

from warehouse_helper import ADMIN, ENGINE, USER, VIEWER

pytestmark = pytest.mark.integration

# What a flow leaves in the warehouse: a table in raw, orig and publish, created by the engine
FLOW = """
    CREATE SCHEMA raw;
    CREATE TABLE raw.series (id TEXT);
    INSERT INTO raw.series VALUES ('1');
    CREATE SCHEMA orig;
    CREATE TABLE orig.series (id INTEGER);
    INSERT INTO orig.series VALUES (1);
    CREATE SCHEMA publish;
    CREATE TABLE publish.series (id INTEGER);
    INSERT INTO publish.series VALUES (1);
"""


@pytest.fixture
def flow(warehouse):
    warehouse.execute(ENGINE, FLOW)
    return warehouse


def test_the_engine_can_do_what_a_flow_does_on_every_run(warehouse):
    """
    Checks: omnis_airflow can do what a run of a flow does, twice: create its schemas, tables and
    functions if they don't exist (or replace them), drop and recreate a raw table, and write rows.

    If it fails: the engine can't run its flows with its own role. create_tables or a raw load would
    fail with "permission denied" or "must be owner", so Airflow would have to go back to the
    superuser, and nothing it writes could be told apart from what a person writes.
    """
    run = """
        CREATE SCHEMA IF NOT EXISTS raw;
        CREATE OR REPLACE FUNCTION raw.null_if_placeholder(value TEXT) RETURNS TEXT
            LANGUAGE sql AS $$ SELECT NULLIF(value, '-') $$;
        DROP TABLE IF EXISTS raw.series;
        CREATE TABLE raw.series (id TEXT);
        INSERT INTO raw.series VALUES ('1'), ('-');
        CREATE SCHEMA IF NOT EXISTS orig;
        CREATE TABLE IF NOT EXISTS orig.series (id INTEGER);
        DELETE FROM orig.series;
        INSERT INTO orig.series SELECT CAST(raw.null_if_placeholder(id) AS INTEGER) FROM raw.series;
    """

    warehouse.execute(ENGINE, run)
    warehouse.execute(ENGINE, run)

    assert warehouse.fetch(ENGINE, "SELECT id FROM orig.series ORDER BY id") == [(1,), (None,)]


@pytest.mark.parametrize(
    "statement",
    [
        "SELECT * FROM raw.series",
        "INSERT INTO orig.series VALUES (2)",
        "UPDATE orig.series SET id = 2",
        "DELETE FROM orig.series",
        "TRUNCATE orig.series",
        "ALTER TABLE orig.series ADD COLUMN peso FLOAT",
        "CREATE INDEX ON orig.series (id)",
        "DROP TABLE publish.series",
        "CREATE TABLE orig.new (id INTEGER)",
        "CREATE SCHEMA clean",
    ],
)
def test_an_admin_can_do_whatever_the_engine_can(flow, statement):
    """
    Checks: a login of database_admin can read, write and change the structure of the tables the
    engine created, and create tables and schemas, as their owner (omnis_airflow) can.

    If it fails: whoever maintains the warehouse by hand couldn't fix a row or apply a change of a
    tables/*.sql to a table that already exists (CREATE TABLE IF NOT EXISTS doesn't alter it). They
    would have to use the superuser, and their changes would no longer be signed with their login.
    """
    flow.execute(ADMIN, statement)


def test_a_user_reads_every_flow_schema_raw_included(flow):
    """
    Checks: a login of database_user reads the tables of every schema of a flow: raw, orig and publish.

    If it fails: the programmers who follow the data from DBeaver couldn't see what was loaded, or
    could only see part of it. raw is included because it is where a wrong value is first traced.
    """
    for table in ["raw.series", "orig.series", "publish.series"]:
        assert flow.fetch(USER, f"SELECT count(*) FROM {table}") == [(1,)], table


def test_visualization_reads_publish(flow):
    """
    Checks: a login of visualization reads the tables of publish.

    If it fails: the dashboards (Apolo) and BI tools couldn't read the data they are built on.
    """
    assert flow.fetch(VIEWER, "SELECT count(*) FROM publish.series") == [(1,)]


@pytest.mark.parametrize("table", ["raw.series", "orig.series"])
def test_visualization_reads_nothing_but_publish(flow, table):
    """
    Checks: a login of visualization can't read the tables of any schema but publish.

    If it fails: a dashboard or a BI tool could read the raw and intermediate layers, and build on
    data that isn't meant to be consumed (untyped, with duplicates or placeholders).
    """
    with pytest.raises(errors.InsufficientPrivilege):
        flow.fetch(VIEWER, f"SELECT * FROM {table}")


@pytest.mark.parametrize("role", [USER, VIEWER])
@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO publish.series VALUES (2)",
        "UPDATE publish.series SET id = 2",
        "DELETE FROM publish.series",
        "TRUNCATE publish.series",
        "ALTER TABLE publish.series ADD COLUMN peso FLOAT",
        "DROP TABLE publish.series",
        "CREATE TABLE publish.new (id INTEGER)",
        "CREATE TABLE public.new (id INTEGER)",
        "CREATE SCHEMA clean",
        "CREATE FUNCTION publish.f() RETURNS INTEGER LANGUAGE sql AS 'SELECT 1'",
    ],
)
def test_a_reader_changes_nothing(flow, role, statement):
    """
    Checks: a login of database_user or of visualization can't write, change or create anything,
    not even in publish, which both can read.

    If it fails: a read-only login could change the data or the structure of the warehouse. A
    connection meant for following data or for a dashboard could break a flow or corrupt its tables.
    """
    with pytest.raises(errors.InsufficientPrivilege):
        flow.execute(role, statement)


def test_the_init_can_be_applied_again(flow):
    """
    Checks: applying the init again, as omnis-database-init does on every start, doesn't fail and
    leaves the owners and permissions of the flow's schemas and tables as they were.

    If it fails: the stack wouldn't start a second time (Airflow waits for the init), or every start
    would change who can do what in the warehouse.
    """
    access = """
        SELECT nspname, nspowner::regrole::text, nspacl::text FROM pg_namespace
        WHERE nspname IN ('raw', 'orig', 'publish')
        UNION ALL
        SELECT oid::regclass::text, relowner::regrole::text, relacl::text FROM pg_class
        WHERE relnamespace::regnamespace::text IN ('raw', 'orig', 'publish')
        ORDER BY 1
    """
    before = flow.fetch(ENGINE, access)

    flow.apply_init()

    assert flow.fetch(ENGINE, access) == before
