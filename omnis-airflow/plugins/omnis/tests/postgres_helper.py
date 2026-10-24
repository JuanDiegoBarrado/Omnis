import csv
from io import BytesIO
from pathlib import Path

import psycopg2
from psycopg2 import sql


def _csv_header(path: Path) -> list[str]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return next(csv.reader(file), [])


class PostgresHelper:
    """
    A database of its own for one test, written and read with psycopg2 directly, so what a test
    sets up and checks doesn't go through the adapters it tests.

    Tables are given and expected as CSV files named `<schema>.<table>.csv`, with a header. An
    unquoted empty value is NULL, as in Postgres's COPY.
    """

    def __init__(self, dsn: str):
        self.dsn = dsn

    def execute(self, query: str, params=None) -> None:
        connection = psycopg2.connect(self.dsn)
        try:
            with connection, connection.cursor() as cursor:
                cursor.execute(query, params)
        finally:
            connection.close()

    def fetch(self, query: str, params=None) -> list[tuple]:
        connection = psycopg2.connect(self.dsn)
        try:
            with connection, connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        finally:
            connection.close()

    def columns(self, table: str) -> list[str]:
        schema, name = table.split(".", 1)
        rows = self.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
            (schema, name),
        )
        return [column for (column,) in rows]

    def load(self, folder: Path) -> None:
        """Insert the rows of every `<schema>.<table>.csv` in `folder` into its table, which must exist."""
        for path in sorted(folder.glob("*.csv")):
            self._copy(path.stem, _csv_header(path), path.read_bytes())

    def assert_tables(self, folder: Path) -> None:
        """Check every table with a `<schema>.<table>.csv` in `folder` against it (see assert_table)."""
        paths = sorted(folder.glob("*.csv"))
        assert paths, f"No expected tables in {folder}"
        for path in paths:
            self.assert_table(path.stem, path)

    def assert_table(self, table: str, expected: Path) -> None:
        """
        Check that `table` holds exactly the rows of the CSV `expected`, in any order, comparing each
        value as Postgres writes it as text. The CSV must have every column of the table.
        """
        header = _csv_header(expected)
        actual_columns = self.columns(table)
        assert sorted(header) == sorted(actual_columns), (
            f"{expected.name}: columns {sorted(header)}, but {table} has {sorted(actual_columns)}"
        )

        columns = sql.SQL(", ").join(sql.Identifier(column) for column in header)
        as_text = sql.SQL(", ").join(sql.SQL("{}::text").format(sql.Identifier(column)) for column in header)
        actual = sql.SQL("SELECT {} FROM {}").format(as_text, sql.Identifier(*table.split(".", 1)))
        connection = psycopg2.connect(self.dsn)
        try:
            with connection, connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE TEMP TABLE expected ({})").format(
                    sql.SQL(", ").join(sql.SQL("{} text").format(sql.Identifier(column)) for column in header)
                ))
                cursor.copy_expert(
                    sql.SQL("COPY expected ({}) FROM STDIN WITH (FORMAT csv, HEADER true)").format(columns).as_string(connection),
                    BytesIO(expected.read_bytes()),
                )
                cursor.execute(sql.SQL("SELECT {} FROM expected EXCEPT ALL {}").format(columns, actual))
                missing = cursor.fetchall()
                cursor.execute(sql.SQL("{} EXCEPT ALL SELECT {} FROM expected").format(actual, columns))
                unexpected = cursor.fetchall()
        finally:
            connection.close()

        assert not missing and not unexpected, (
            f"{table} differs from {expected.name} (columns {header}):\n"
            f"  missing rows:    {missing}\n"
            f"  unexpected rows: {unexpected}"
        )

    def _copy(self, table: str, columns: list[str], content: bytes) -> None:
        connection = psycopg2.connect(self.dsn)
        try:
            with connection, connection.cursor() as cursor:
                copy = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT csv, HEADER true)").format(
                    sql.Identifier(*table.split(".", 1)),
                    sql.SQL(", ").join(sql.Identifier(column) for column in columns),
                )
                cursor.copy_expert(copy.as_string(connection), BytesIO(content))
        finally:
            connection.close()
