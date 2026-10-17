import pytest

from omnis.adapters import SqlEtlExecutor
from omnis.domain import Etl, Pipe, RawLoad, Table, WriteStrategy
from omnis.ports import Database


class FakeDatabase(Database):
    """Records every statement instead of talking to a real database."""

    def __init__(self, pipe_columns=None):
        self.pipe_columns = pipe_columns or []
        self.statements: list[str] = []
        self.copies: list[tuple] = []
        self.connections = 0

    def __enter__(self):
        self.connections += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def execute_sql(self, query, params=None):
        self.statements.append(query)
        return 3

    def fetch_all(self, query, params=None):
        self.statements.append(query)
        return []

    def fetch_all_with_columns(self, query, params=None):
        self.statements.append(query)
        return [], self.pipe_columns

    def copy_csv(self, table_name, columns, content):
        self.copies.append((table_name, columns, content))
        return content.count(b"\n") - 1


PIPE = Pipe(name="orig.x", query="SELECT fecha, num, peso FROM raw.x")


def test_full_rebuild_replaces_the_destination_with_the_pipe_rows_between_the_hooks():
    database = FakeDatabase(pipe_columns=["fecha", "num", "peso"])
    etl = Etl(name="orig.x", destination="orig.x", pipe="orig.x", pre_statement="PRE", post_statement="POST")

    written = SqlEtlExecutor(database).run(etl, PIPE)

    assert written == 3
    assert database.connections == 1
    assert database.statements == [
        "PRE",
        "SELECT * FROM (\nSELECT fecha, num, peso FROM raw.x\n) AS pipe LIMIT 0",
        'DELETE FROM "orig"."x"',
        'INSERT INTO "orig"."x" ("fecha", "num", "peso")\n'
        'SELECT "fecha", "num", "peso" FROM (\nSELECT fecha, num, peso FROM raw.x\n) AS pipe',
        "POST",
    ]


def test_merge_updates_matching_keys_and_inserts_the_rest():
    database = FakeDatabase(pipe_columns=["fecha", "num", "peso"])
    etl = Etl(name="orig.x", destination="orig.x", pipe="orig.x", strategy=WriteStrategy.MERGE, key=("fecha", "num"))

    SqlEtlExecutor(database).run(etl, PIPE)

    assert database.statements[-1] == (
        'MERGE INTO "orig"."x" AS target\n'
        "USING (\nSELECT fecha, num, peso FROM raw.x\n) AS source\n"
        'ON target."fecha" = source."fecha" AND target."num" = source."num"\n'
        'WHEN MATCHED THEN UPDATE SET "peso" = source."peso"\n'
        'WHEN NOT MATCHED THEN INSERT ("fecha", "num", "peso") VALUES (source."fecha", source."num", source."peso")'
    )


def test_merge_fails_when_the_pipe_does_not_produce_the_key():
    database = FakeDatabase(pipe_columns=["fecha", "peso"])
    etl = Etl(name="orig.x", destination="orig.x", pipe="orig.x", strategy=WriteStrategy.MERGE, key=("fecha", "num"))

    with pytest.raises(ValueError, match="num"):
        SqlEtlExecutor(database).run(etl, PIPE)


def test_load_raw_recreates_the_landing_table_and_copies_every_csv_by_its_header():
    database = FakeDatabase()
    raw_load = RawLoad(name="raw.x", source="raw/new/x/", destination="raw.x", columns=("fecha", "num", "rir"))
    files = [
        ("raw/new/x/a.csv", b"Fecha,RIR\n2026-01-01,2\n"),
        ("raw/new/x/notes.txt", b"ignored"),
        ("raw/new/x/empty.csv", b""),
    ]

    loaded = SqlEtlExecutor(database).load_raw(raw_load, files)

    assert loaded == 1
    assert database.statements == [
        'CREATE SCHEMA IF NOT EXISTS "raw"',
        'DROP TABLE IF EXISTS "raw"."x"',
        'CREATE TABLE "raw"."x" ("fecha" TEXT, "num" TEXT, "rir" TEXT)',
    ]
    assert database.copies == [("raw.x", ["fecha", "rir"], b"Fecha,RIR\n2026-01-01,2\n")]


def test_load_raw_rejects_files_with_undeclared_columns():
    raw_load = RawLoad(name="raw.x", source="raw/new/x/", destination="raw.x", columns=("fecha",))

    with pytest.raises(ValueError, match="peso"):
        SqlEtlExecutor(FakeDatabase()).load_raw(raw_load, [("raw/new/x/a.csv", b"fecha,peso\n2026-01-01,80\n")])


def test_create_tables_applies_every_ddl_in_one_transaction():
    database = FakeDatabase()

    SqlEtlExecutor(database).create_tables([Table("orig.x", "CREATE A"), Table("orig.y", "CREATE B")])

    assert database.connections == 1
    assert database.statements == ["CREATE A", "CREATE B"]
