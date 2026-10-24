import pytest
from psycopg2 import errors

from omnis.adapters import PostgresDatabase, SqlDdlRunner
from omnis.domain import DDL, Table

pytestmark = pytest.mark.integration

ORIG_A = Table("orig.a", "CREATE SCHEMA IF NOT EXISTS orig; CREATE TABLE IF NOT EXISTS orig.a (id INT);")
ORIG_B = Table("orig.b", "CREATE SCHEMA IF NOT EXISTS orig; CREATE TABLE IF NOT EXISTS orig.b (id INT);")


def run(postgres, *tables: Table) -> int:
    ddl = DDL(tables=tables, runner=SqlDdlRunner(PostgresDatabase(postgres.dsn)))
    return ddl.runner.run(ddl)


def tables_in(postgres, schema: str) -> list[str]:
    rows = postgres.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = %s ORDER BY 1", (schema,))
    return [name for (name,) in rows]


def test_applies_the_ddl_of_every_table_and_can_be_applied_again(postgres):
    """
    Checks: create_tables applies the DDL of every table, and applying it again on the next run
    keeps the tables and their rows.

    If it fails: some table would not be created (its writer fails), or the second run of the DAG
    would fail or wipe the tables, since create_tables runs at the start of every run.
    """
    assert run(postgres, ORIG_A, ORIG_B) == 2
    postgres.execute("INSERT INTO orig.a VALUES (1)")

    run(postgres, ORIG_A, ORIG_B)

    assert tables_in(postgres, "orig") == ["a", "b"]
    assert postgres.fetch("SELECT id FROM orig.a") == [(1,)]


def test_a_failing_ddl_applies_none(postgres):
    """
    Checks: if the DDL of one table fails, none of the DDL of that run is applied.

    If it fails: a broken DDL file would leave the database half migrated (some tables changed,
    others not), and the next tasks would run against a mixed schema.
    """
    broken = Table("orig.broken", "CREATE TABLE orig.broken (id NOT_A_TYPE);")

    with pytest.raises(errors.UndefinedObject):
        run(postgres, ORIG_A, broken)

    assert tables_in(postgres, "orig") == []
