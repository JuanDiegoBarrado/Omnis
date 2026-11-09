"""
How each object of the flows' schemas gets its owner (omnis_airflow) and its readers, whoever creates
it: when it is created (the event trigger of 02_access.sql), or when the init starts, if it already
existed (its sweep).
"""
import pytest
from psycopg2 import errors

from warehouse_helper import ADMIN, ENGINE, SUPERUSER, USER, VIEWER

pytestmark = pytest.mark.integration


def test_what_an_admin_creates_belongs_to_the_engine(warehouse):
    """
    Checks: a schema, a table, a view and a function that a login of database_admin creates belong to
    omnis_airflow, not to that login, so the engine can alter or replace them, and database_user
    can read the table and the view.

    If it fails: an object created by hand would belong to the person who created it. The engine
    would fail on its next run when it replaces it (CREATE OR REPLACE needs the owner), and the
    readers couldn't see it, until someone changed its owner by hand.
    """
    warehouse.execute(ADMIN, """
        CREATE SCHEMA clean;
        CREATE TABLE clean.series (id INTEGER);
        INSERT INTO clean.series VALUES (1);
        CREATE VIEW clean.series_view AS SELECT id FROM clean.series;
        CREATE FUNCTION clean.one() RETURNS INTEGER LANGUAGE sql AS 'SELECT 1';
    """)

    assert warehouse.owner("schema", "clean") == ENGINE
    assert warehouse.owner("relation", "clean.series") == ENGINE
    assert warehouse.owner("relation", "clean.series_view") == ENGINE
    assert warehouse.owner("routine", "clean.one()") == ENGINE
    warehouse.execute(ENGINE, """
        ALTER TABLE clean.series ADD COLUMN peso FLOAT;
        CREATE OR REPLACE VIEW clean.series_view AS SELECT id, peso FROM clean.series;
        CREATE OR REPLACE FUNCTION clean.one() RETURNS INTEGER LANGUAGE sql AS 'SELECT 1';
    """)
    assert warehouse.fetch(USER, "SELECT id FROM clean.series_view") == [(1,)]


def test_a_raw_table_recreated_on_every_run_can_still_be_read(warehouse):
    """
    Checks: a raw table that the engine drops and creates again, as a raw load does on every run,
    can be read by database_user after each time.

    If it fails: permissions belong to a table, so they die with it. After the first raw load, the
    raw tables could no longer be read by the programmers who trace where a value came from.
    """
    warehouse.execute(ENGINE, "CREATE SCHEMA raw; CREATE TABLE raw.series (id TEXT)")
    warehouse.execute(ENGINE, "DROP TABLE raw.series; CREATE TABLE raw.series (id TEXT, fecha TEXT)")

    assert warehouse.fetch(USER, "SELECT id, fecha FROM raw.series") == []


def test_only_the_tables_of_publish_are_visible_to_visualization(warehouse):
    """
    Checks: a table the engine creates in publish can be read by visualization, and one it creates
    in any other schema can't, even when that schema is created after publish.

    If it fails: the permissions of visualization would depend on the order in which a flow creates
    its schemas, and a dashboard could lose publish or see the layers it isn't meant to.
    """
    warehouse.execute(ENGINE, """
        CREATE SCHEMA publish;
        CREATE TABLE publish.series (id INTEGER);
        CREATE SCHEMA clean;
        CREATE TABLE clean.series (id INTEGER);
    """)

    assert warehouse.fetch(VIEWER, "SELECT * FROM publish.series") == []
    with pytest.raises(errors.InsufficientPrivilege):
        warehouse.fetch(VIEWER, "SELECT * FROM clean.series")


def test_the_init_claims_what_existed_before_it(database):
    """
    Checks: schemas, tables, views and functions created before the init (here by the superuser, as
    Airflow did before it had a role of its own) become omnis_airflow's when the init is applied,
    with the same permissions as if they had been created after it.

    If it fails: a warehouse that already had data when the init arrived (or one restored with the
    event trigger off) would keep its old owners. The engine couldn't write to its own tables or
    replace its functions, and the readers couldn't see them.
    """
    database.execute(SUPERUSER, """
        CREATE SCHEMA raw;
        CREATE FUNCTION raw.null_if_placeholder(value TEXT) RETURNS TEXT LANGUAGE sql AS 'SELECT value';
        CREATE SCHEMA orig;
        CREATE TABLE orig.series (id INTEGER);
        INSERT INTO orig.series VALUES (1);
        CREATE SCHEMA publish;
        CREATE VIEW publish.series AS SELECT id FROM orig.series;
    """)

    database.apply_init()

    assert database.owner("schema", "orig") == ENGINE
    assert database.owner("relation", "orig.series") == ENGINE
    assert database.owner("relation", "publish.series") == ENGINE
    assert database.owner("routine", "raw.null_if_placeholder(text)") == ENGINE
    database.execute(ENGINE, """
        CREATE OR REPLACE FUNCTION raw.null_if_placeholder(value TEXT) RETURNS TEXT
            LANGUAGE sql AS $$ SELECT NULLIF(value, '-') $$;
        INSERT INTO orig.series VALUES (2);
    """)
    assert database.fetch(USER, "SELECT count(*) FROM orig.series") == [(2,)]
    assert database.fetch(VIEWER, "SELECT count(*) FROM publish.series") == [(2,)]


def test_a_reader_can_still_use_temporary_tables(warehouse):
    """
    Checks: a login of database_user can create a temporary table and use it, although it can't
    create anything else: the event trigger leaves temporary tables alone.

    If it fails: the event trigger would fail for every temporary table of a reader (it would try
    to give it to omnis_airflow without being able to), so the programmers couldn't use temporary
    tables in their queries.
    """
    warehouse.execute(USER, "CREATE TEMP TABLE scratch (id INTEGER); INSERT INTO scratch VALUES (1)")


def test_public_is_left_alone(warehouse):
    """
    Checks: a table the superuser creates in public keeps its owner, and the readers don't get to
    read it: public is not a schema of the flows.

    If it fails: the init would take over what isn't the flows' (what the superuser or an extension
    keeps in public) and hand it to the engine and to every reader.
    """
    warehouse.execute(SUPERUSER, "CREATE TABLE public.private (id INTEGER)")

    assert warehouse.owner("relation", "public.private") == warehouse.server.superuser
    with pytest.raises(errors.InsufficientPrivilege):
        warehouse.fetch(USER, "SELECT * FROM public.private")
