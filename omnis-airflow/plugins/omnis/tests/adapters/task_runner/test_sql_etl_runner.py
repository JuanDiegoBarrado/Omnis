"""
What every ETL does whatever its strategy. Every test starts from the tables in given/; when an
ETL fails, the destination must be left exactly as it was.
"""
from pathlib import Path

import pytest
from psycopg2 import errors

from omnis.adapters import PostgresDatabase, SqlEtlRunner
from omnis.domain import Etl, Pipe, WriteStrategy

pytestmark = pytest.mark.integration

DATA = Path(__file__).with_suffix("")

PIPE = "SELECT CAST(id AS INTEGER) AS id, CAST(fecha AS DATE) AS fecha, CAST(peso AS FLOAT) AS peso FROM src.origin"


@pytest.fixture
def postgres(postgres):
    postgres.execute((DATA / "tables.sql").read_text(encoding="utf-8"))
    postgres.load(DATA / "given")
    return postgres


def run(postgres, query: str, strategy=WriteStrategy.MERGE, **etl_arguments) -> int:
    etl = Etl(
        "dst.destination",
        destination="dst.destination",
        pipe=Pipe("dst.destination", query),
        strategy=strategy,
        key=("id",) if strategy is WriteStrategy.MERGE else (),
        runner=SqlEtlRunner(PostgresDatabase(postgres.dsn)),
        **etl_arguments,
    )
    return etl.runner.run(etl)


@pytest.mark.parametrize("strategy", list(WriteStrategy))
def test_the_columns_of_the_pipe_are_written_by_name_not_position(postgres, strategy):
    """
    Checks: the pipe's columns go to the destination columns with the same name, even when the
    pipe returns them in another order (peso, fecha, id against id, fecha, peso).

    If it fails: the runner writes by position. A pipe whose SELECT doesn't follow the order of the
    table's DDL would put each value in the wrong column (weights as ids...) or fail on types.
    """
    reordered = "SELECT peso, fecha, id FROM (" + PIPE + ") AS typed"
    if strategy is WriteStrategy.FULL_REBUILD:
        reordered += " UNION ALL SELECT 80, DATE '2026-01-01', 1"

    run(postgres, reordered, strategy)

    postgres.assert_table("dst.destination", DATA / "columns_matched_by_name" / "dst.destination.csv")


def test_runs_its_statements_before_and_after_writing(postgres):
    """
    Checks: pre_statement runs before the pipe is written (it deletes id 1) and post_statement runs
    after it (it doubles every weight, including the merged ones).

    If it fails: the hooks don't run, or run in the wrong order, so ETLs relying on them would leave
    their destination different from what was declared.
    """
    run(
        postgres,
        PIPE,
        pre_statement="DELETE FROM dst.destination WHERE id = 1",
        post_statement="UPDATE dst.destination SET peso = peso * 2",
    )

    postgres.assert_table("dst.destination", DATA / "statements" / "dst.destination.csv")


@pytest.mark.parametrize("strategy", list(WriteStrategy))
def test_a_failing_post_statement_leaves_the_destination_as_it_was(postgres, strategy):
    """
    Checks: if post_statement fails after the rows were written, everything is undone: the
    destination keeps exactly its rows from before the ETL.

    If it fails: the ETL is not atomic. A full rebuild that fails after its DELETE would leave the
    destination empty or half written, and a merge would leave partial changes. Both would go
    unnoticed until someone looks at the data.
    """
    with pytest.raises(errors.UndefinedTable):
        run(postgres, PIPE, strategy, post_statement="UPDATE dst.missing SET x = 1")

    postgres.assert_tables(DATA / "given")


@pytest.mark.parametrize("strategy", list(WriteStrategy))
def test_a_pipe_failing_on_some_row_leaves_the_destination_as_it_was(postgres, strategy):
    """
    Checks: if the pipe fails halfway (a division by zero on one row, like a bad CAST of a raw
    value), the destination keeps exactly its rows from before the ETL.

    If it fails: one bad raw row would leave the destination emptied (full rebuild) or partially
    merged, instead of failing the task and leaving the data as it was.
    """
    failing = PIPE.replace("CAST(peso AS FLOAT)", "CAST(peso AS FLOAT) / (CAST(id AS INTEGER) - 3)")

    with pytest.raises(errors.DivisionByZero):
        run(postgres, failing, strategy)

    postgres.assert_tables(DATA / "given")


@pytest.mark.parametrize("duplicated_id", [2, 3], ids=["already_loaded", "new"])
def test_a_merge_whose_pipe_returns_a_key_twice_fails_and_writes_nothing(postgres, duplicated_id):
    """
    Checks: a merge whose pipe returns the same key twice fails before writing anything, both for
    a key the destination already has ([already_loaded]) and for a new one ([new]).

    If it fails: Postgres's MERGE only errors when one destination row matches two pipe rows. A new
    key returned twice matches nothing, so both rows would be inserted: the destination (an orig
    table, the history) would hold duplicates forever, without any error. Only a PRIMARY KEY in the
    DDL would stop that, and the engine must not depend on every flow declaring one.
    """
    duplicated = f"{PIPE} UNION ALL SELECT {duplicated_id}, DATE '2026-02-01', 100"

    with pytest.raises(ValueError, match="more than once"):
        run(postgres, duplicated)

    postgres.assert_tables(DATA / "given")


def test_a_merge_whose_pipe_returns_a_null_key_fails_and_writes_nothing(postgres):
    """
    Checks: a merge whose pipe returns a row with a NULL key fails before writing anything.

    If it fails: `NULL = NULL` is not true in SQL, so a NULL key never matches and its row would be
    inserted again every time the ETL runs on the same data (a retry, a cleared run). The merge
    would stop being idempotent, and the destination would fill up with copies of that row.
    """
    with_null_key = f"{PIPE} UNION ALL SELECT NULL, DATE '2026-02-01', 100"

    with pytest.raises(ValueError, match="or NULL"):
        run(postgres, with_null_key)

    postgres.assert_tables(DATA / "given")


def test_a_merge_whose_key_the_pipe_does_not_return_fails_and_writes_nothing(postgres):
    """
    Checks: a merge whose key columns are not among the pipe's columns fails with an error that names
    them, before writing anything.

    If it fails: a pipe that renamed or dropped a key column would fail with an obscure SQL error,
    or worse, merge on the wrong columns.
    """
    with pytest.raises(ValueError, match=r"key columns \['id'\]"):
        run(postgres, "SELECT CAST(fecha AS DATE) AS fecha FROM src.origin")

    postgres.assert_tables(DATA / "given")
