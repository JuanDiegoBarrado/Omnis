"""
The traceability of the warehouse (03_tracking.sql): when each row of a flow's table was inserted
and last changed, and by whom (sys_fec_insert, sys_fec_mod, sys_blame), kept by the database itself
whoever writes. Times are checked against the transaction that wrote them (now() is the start of
the transaction), never against a fixed value.
"""
import pytest
from psycopg2 import errors

from warehouse_helper import ADMIN, ENGINE, SUPERUSER, USER, VIEWER

pytestmark = pytest.mark.integration

SYSTEM_COLUMNS = ["sys_fec_insert", "sys_fec_mod", "sys_blame"]

# A table of orig as a flow creates it, with a row loaded by the engine from file_1
ORIG = """
    CREATE SCHEMA orig;
    CREATE TABLE orig.series (id INTEGER PRIMARY KEY, peso FLOAT, sys_source_file TEXT);
"""
LOADED = "INSERT INTO orig.series (id, peso, sys_source_file) VALUES (1, 80, 'file_1')"
ROW = "SELECT xmin::text, * FROM orig.series ORDER BY id"


@pytest.fixture
def orig(warehouse):
    warehouse.execute(ENGINE, ORIG)
    return warehouse


@pytest.fixture
def loaded(orig):
    orig.execute(ENGINE, LOADED)
    return orig


def sign(detail: str | None) -> str:
    """What a writer runs to sign its transaction with `detail`, as the engine does (or nothing)."""
    return f"SELECT set_config('omnis.blame', '{detail}', true);" if detail else ""


@pytest.mark.parametrize(
    "role, detail, blame",
    [
        (ENGINE, "health/manual__1", "omnis_airflow:health/manual__1"),
        (ENGINE, None, "omnis_airflow"),
        (ADMIN, "fix of 2026-10", "an_admin:fix of 2026-10"),
        (ADMIN, None, "an_admin"),
    ],
)
def test_an_insert_records_when_and_who(orig, role, detail, blame):
    """
    Checks: a row inserted gets as sys_fec_insert and sys_fec_mod the time of its transaction, and as
    sys_blame the login that inserted it, followed by the detail it signed its transaction with, if
    any (`<login>:<detail>`): the engine signs `<flow>/<run_id>`, a person whatever they want.

    If it fails: the warehouse couldn't tell when a row arrived or who wrote it: neither the run of
    Airflow (and so its files and logs) nor the person who inserted it by hand.
    """
    rows = orig.fetch(role, f"""
        {sign(detail)}
        INSERT INTO orig.series (id, peso) VALUES (1, 80);
        SELECT sys_fec_insert = now(), sys_fec_mod = now(), sys_blame FROM orig.series;
    """)

    assert rows == [(True, True, blame)]


def test_an_insert_cannot_choose_its_system_columns(orig):
    """
    Checks: the values an INSERT gives to the system columns are ignored: the row gets the time of
    its transaction and the login that inserted it.

    If it fails: anyone could insert rows that claim to be older or written by someone else (another
    login, a run of Airflow), and the traceability would be worth nothing.
    """
    rows = orig.fetch(ADMIN, """
        INSERT INTO orig.series (id, peso, sys_fec_insert, sys_fec_mod, sys_blame)
        VALUES (1, 80, '2000-01-01', '2000-01-01', 'omnis_airflow:health/manual__1');
        SELECT sys_fec_insert = now(), sys_fec_mod = now(), sys_blame FROM orig.series;
    """)

    assert rows == [(True, True, "an_admin")]


def test_an_update_records_when_and_who_but_keeps_when_it_was_inserted(loaded):
    """
    Checks: a row updated with a value of its own changed keeps its sys_fec_insert, and gets as
    sys_fec_mod the time of the update and as sys_blame who updated it, even when the UPDATE tries to
    set them itself.

    If it fails: an update would lose when the row arrived, or let whoever updates a row choose the
    time and the author of the change, so a correction could pass for the original load.
    """
    [(inserted,)] = loaded.fetch(SUPERUSER, "SELECT sys_fec_insert FROM orig.series")

    rows = loaded.fetch(ADMIN, """
        UPDATE orig.series
        SET peso = 85, sys_fec_insert = '2000-01-01', sys_fec_mod = '2000-01-01', sys_blame = 'omnis_airflow';
        SELECT sys_fec_insert, sys_fec_mod = now(), sys_fec_mod > sys_fec_insert, sys_blame FROM orig.series;
    """)

    assert rows == [(inserted, True, True, "an_admin")]


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE orig.series SET peso = 80",
        "UPDATE orig.series SET sys_source_file = 'file_2'",
        "UPDATE orig.series SET sys_blame = 'someone', sys_fec_mod = now()",
        """
        MERGE INTO orig.series AS target
        USING (SELECT 1 AS id, CAST(80 AS FLOAT) AS peso, 'file_2' AS sys_source_file) AS source
        ON target.id = source.id
        WHEN MATCHED THEN UPDATE SET peso = source.peso, sys_source_file = source.sys_source_file
        """,
    ],
    ids=["same_values", "only_the_file", "only_system_columns", "merge_with_the_same_values"],
)
def test_an_update_that_changes_nothing_is_skipped(loaded, statement):
    """
    Checks: an UPDATE (or a MERGE) that leaves every column the same, but maybe the system ones
    (sys_*, like sys_source_file), is skipped for that row: it isn't counted, and the row keeps
    everything (xmin included, so it isn't even rewritten). Cases: [same_values], [only_the_file]
    (the same row from another file), [only_system_columns] (an attempt to rewrite the traceability)
    and [merge_with_the_same_values] (a merge that doesn't compare, like the engine's before it did).

    If it fails: a row loaded again would look modified by that run, so the warehouse could no longer
    tell when or by whom a row really changed. And anyone could rewrite the author or the time of a
    change, or the file a row came from, without changing the row.
    """
    before = loaded.fetch(SUPERUSER, ROW)

    assert loaded.execute(ADMIN, statement) == 0

    assert loaded.fetch(SUPERUSER, ROW) == before


def test_a_signature_ends_with_its_transaction(orig):
    """
    Checks: what a session writes after the transaction it signed in (with set_config(..., true),
    as the engine does, or SET LOCAL) is blamed on the login alone, not on the old detail nor on
    `<login>:` with an empty one.

    If it fails: a person who signed one transaction would sign everything after it in the same
    session (a DBeaver connection kept open for hours), or their rows would end in a dangling ':'.
    """
    connection = orig.connect(ENGINE)
    try:
        with connection, connection.cursor() as cursor:
            cursor.execute(sign("health/manual__1") + "INSERT INTO orig.series (id) VALUES (1)")
        with connection, connection.cursor() as cursor:
            cursor.execute("INSERT INTO orig.series (id) VALUES (2)")
    finally:
        connection.close()

    assert orig.fetch(SUPERUSER, "SELECT id, sys_blame FROM orig.series ORDER BY id") == [
        (1, "omnis_airflow:health/manual__1"),
        (2, "omnis_airflow"),
    ]


def test_set_role_does_not_hide_who_writes(orig):
    """
    Checks: a login of database_admin that switches to omnis_airflow (SET ROLE, which its group
    allows) and writes is still blamed with its own login.

    If it fails: an admin could write as if they were the engine, and their changes by hand would be
    mistaken for a run of Airflow.
    """
    rows = orig.fetch(ADMIN, """
        SET ROLE omnis_airflow;
        INSERT INTO orig.series (id) VALUES (1);
        SELECT current_user::text, sys_blame FROM orig.series;
    """)

    assert rows == [("omnis_airflow", "an_admin")]


@pytest.mark.parametrize("creator", [ENGINE, ADMIN, SUPERUSER])
def test_a_new_table_is_tracked_whoever_creates_it(warehouse, creator):
    """
    Checks: a table created in a schema of the flows (by the engine, an admin or the superuser) gets
    the system columns and the trigger that keeps them, as soon as it is created.

    If it fails: the tables that the flows create on their first run, or that someone adds by hand,
    would have no traceability, and nothing would tell, since the columns would simply be missing.
    """
    warehouse.execute(creator, "CREATE SCHEMA clean; CREATE TABLE clean.series (id INTEGER)")

    assert warehouse.tracking("clean.series") == (SYSTEM_COLUMNS, True)


def test_raw_tables_are_not_tracked(warehouse):
    """
    Checks: a table the engine creates in raw gets no system columns nor trigger.

    If it fails: raw tables are recreated on every load with exactly the columns of their files, and
    the raw load matches CSV columns by name. Extra columns there would be noise in a layer that
    already records the file of each row.
    """
    warehouse.execute(ENGINE, "CREATE SCHEMA raw; CREATE TABLE raw.series (id TEXT)")

    assert warehouse.tracking("raw.series") == ([], False)


def test_temporary_tables_are_not_tracked(warehouse):
    """
    Checks: a temporary table, which lives in a schema of its session, gets no system columns.

    If it fails: every temporary table of a query (of a person, or a runner in the future) would get
    columns it didn't ask for, and the event trigger would run on what isn't the flows'.
    """
    rows = warehouse.fetch(ENGINE, """
        CREATE TEMP TABLE scratch (id INTEGER);
        SELECT count(*) FROM pg_attribute WHERE attrelid = 'scratch'::regclass AND attname::text LIKE 'sys\\_%';
    """)

    assert rows == [(0,)]


def test_a_table_created_with_rows_blames_them_on_who_created_it(warehouse):
    """
    Checks: the rows of a table created from a query (CREATE TABLE AS) get the time of that
    transaction and the login that created it, signed or not, not 'unknown'.

    If it fails: a table an admin creates from another one would claim its rows were written by
    someone unknown, before the warehouse kept track, although it knows who and when.
    """
    rows = warehouse.fetch(ADMIN, """
        CREATE SCHEMA clean;
        CREATE TABLE clean.series AS SELECT 1 AS id;
        SELECT sys_fec_insert = now(), sys_fec_mod = now(), sys_blame FROM clean.series;
    """)

    assert rows == [(True, True, "an_admin")]


def test_the_init_tracks_the_tables_that_existed_before_it(database):
    """
    Checks: a table of a flow that already had rows when the init was first applied gets the system
    columns: its old rows say 'unknown' in sys_blame, with the time of the init as both dates, and a
    raw table is left as it was. Applying the init again changes nothing (not even rewrites a row),
    and from then on the rows are tracked as any other.

    If it fails: a warehouse that had data before the traceability (or a future system column)
    would be left without it, or its old rows would claim an author they never had. Or every start of
    the stack would rewrite every table.
    """
    database.execute(SUPERUSER, ORIG + LOADED + "; CREATE SCHEMA raw; CREATE TABLE raw.series (id TEXT)")

    database.apply_init()

    assert database.fetch(SUPERUSER, "SELECT sys_fec_insert = sys_fec_mod, sys_blame FROM orig.series") == [
        (True, "unknown")
    ]
    assert database.tracking("raw.series") == ([], False)
    before = database.fetch(SUPERUSER, ROW)
    database.apply_init()
    assert database.fetch(SUPERUSER, ROW) == before
    database.execute(ENGINE, "UPDATE orig.series SET peso = 85")
    assert database.fetch(SUPERUSER, "SELECT sys_blame FROM orig.series") == [("omnis_airflow",)]


@pytest.mark.parametrize("role", [USER, VIEWER])
def test_a_reader_cannot_turn_the_tracking_off(warehouse, role):
    """
    Checks: a login of database_user or of visualization can't disable the trigger of a table it can
    read (one of publish).

    If it fails: a read-only login could switch the traceability off, for itself or for everyone,
    and the rows written meanwhile would have no reliable author or times. Only the superuser and
    database_admin, as the owner's members, can.
    """
    warehouse.execute(ENGINE, "CREATE SCHEMA publish; CREATE TABLE publish.series (id INTEGER)")

    with pytest.raises(errors.InsufficientPrivilege):
        warehouse.execute(role, "ALTER TABLE publish.series DISABLE TRIGGER sys_track_changes")
