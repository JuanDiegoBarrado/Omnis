import logging
from io import BytesIO

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection

from omnis.ports import Database

logger = logging.getLogger(__name__)


class PostgresDatabase(Database):
    """Database over PostgreSQL, through psycopg2."""

    _dsn: str
    _conn: connection | None

    def __init__(self, dsn: str):
        self._dsn = dsn
        self._conn = None

    def __enter__(self) -> "PostgresDatabase":
        logger.info("SQL: Opening database connection")
        self._conn = psycopg2.connect(self._dsn)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._conn is None:
            return
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        self._conn.close()
        self._conn = None
        logger.info("SQL: Closed database connection")

    def _require_conn(self) -> connection:
        """Return the live connection, failing clearly if used outside a 'with' block."""
        if self._conn is None:
            raise RuntimeError("PostgresDatabase must be used within a 'with' block")
        return self._conn

    def execute_sql(self, query: str, params=None) -> int:
        logger.info(f"SQL: Executing statement:\n{query}")
        with self._require_conn().cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def fetch_all(self, query: str, params=None) -> list[tuple]:
        logger.info(f"SQL: Executing query:\n{query}")
        with self._require_conn().cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def fetch_all_with_columns(self, query: str, params=None) -> tuple[list[tuple], list[str]]:
        logger.info(f"SQL: Executing query:\n{query}")
        with self._require_conn().cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in (cursor.description or [])]
            return rows, columns

    def copy_csv(self, table_name: str, columns: list[str], content: bytes) -> int:
        schema_name, table_only = table_name.split(".", 1)
        copy_sql = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')").format(
            sql.Identifier(schema_name, table_only),
            sql.SQL(", ").join(sql.Identifier(col) for col in columns),
        )

        conn = self._require_conn()
        logger.info(f"SQL: Copying CSV into {table_name}")
        with conn.cursor() as cursor:
            cursor.copy_expert(copy_sql.as_string(conn), BytesIO(content))
            return cursor.rowcount
