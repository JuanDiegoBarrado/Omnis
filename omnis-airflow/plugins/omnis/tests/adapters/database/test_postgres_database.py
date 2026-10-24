import pytest

from omnis.adapters import PostgresDatabase

pytestmark = pytest.mark.integration


@pytest.fixture
def database(postgres) -> PostgresDatabase:
    postgres.execute("CREATE TABLE public.t (id INT, value TEXT)")
    return PostgresDatabase(postgres.dsn)


def test_commits_when_the_block_succeeds(postgres, database):
    """
    Checks: what is written inside a `with database` block is committed when the block ends
    without error, and execute_sql returns the affected rows.

    If it fails: every runner writes inside one of these blocks. Their work would be lost when the
    connection closes, and tasks would succeed without leaving any data.
    """
    with database as db:
        assert db.execute_sql("INSERT INTO public.t VALUES (1, 'a'), (2, 'b')") == 2

    assert postgres.fetch("SELECT id, value FROM public.t ORDER BY id") == [(1, "a"), (2, "b")]


def test_rolls_everything_back_when_the_block_fails(postgres, database):
    """
    Checks: if anything inside a `with database` block raises, everything the block did is undone
    (here a DELETE of every row and an INSERT) and the error is raised again.

    If it fails: this is what keeps each task atomic. A task failing halfway would leave tables
    half written: a full rebuild could leave its destination emptied by the DELETE, which is data loss.
    """
    postgres.execute("INSERT INTO public.t VALUES (1, 'kept')")

    with pytest.raises(RuntimeError, match="boom"):
        with database as db:
            db.execute_sql("DELETE FROM public.t")
            db.execute_sql("INSERT INTO public.t VALUES (2, 'lost')")
            raise RuntimeError("boom")

    assert postgres.fetch("SELECT id, value FROM public.t") == [(1, "kept")]


def test_fetches_rows_and_their_columns(postgres, database):
    """
    Checks: fetch_all returns the rows of a query, with its parameters bound, and
    fetch_all_with_columns also returns the names of its columns.

    If it fails: the ETL runner gets the pipe's columns with fetch_all_with_columns, and the archive
    gets the loaded files with fetch_all. They would write the wrong columns or move the wrong files.
    """
    postgres.execute("INSERT INTO public.t VALUES (1, 'a')")

    with database as db:
        assert db.fetch_all("SELECT id FROM public.t WHERE value = %s", ("a",)) == [(1,)]
        assert db.fetch_all_with_columns("SELECT id, value AS v FROM public.t") == ([(1, "a")], ["id", "v"])


def test_copies_csv_into_the_columns_given(postgres, database):
    """
    Checks: copy_csv loads CSV bytes (with BOM and header) into the columns given, in the order of
    the CSV, keeps quoted commas in their value, turns empty values into NULL and returns the rows.

    If it fails: raw loads (which use copy_csv) would put values in the wrong columns, split values
    with commas, or land empty cells as '' instead of NULL. The orig pipes would then type them wrong.
    """
    with database as db:
        loaded = db.copy_csv("public.t", ["value", "id"], "﻿value,id\na,1\n\"b, c\",2\n,3\n".encode("utf-8"))

    assert loaded == 3
    assert postgres.fetch("SELECT id, value FROM public.t ORDER BY id") == [(1, "a"), (2, "b, c"), (3, None)]


def test_cannot_be_used_outside_a_with_block(database):
    """
    Checks: running SQL outside a `with database` block fails with a clear RuntimeError.

    If it fails: code using the database without a transaction would fail with an obscure error, or
    end up running outside the commit/rollback that keeps tasks atomic.
    """
    with pytest.raises(RuntimeError, match="within a 'with' block"):
        database.execute_sql("SELECT 1")
