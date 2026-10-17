import csv
import io
import logging
from collections.abc import Iterable

from omnis.domain import Etl, Pipe, RawLoad, Table, WriteStrategy
from omnis.ports import Database, EtlExecutor

logger = logging.getLogger(__name__)


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _quote_table(table: str) -> str:
    return ".".join(_quote(part) for part in table.split(".", 1))


def _csv_header(content: bytes) -> list[str]:
    first_line = content.decode("utf-8-sig").splitlines()[:1]
    header = next(csv.reader(first_line), [])
    return [column.strip().lower() for column in header]


class SqlEtlExecutor(EtlExecutor):
    """
    EtlExecutor over a relational database (PostgreSQL syntax).

    A pipe is a SELECT, embedded as a subquery: its output columns are written into the
    destination columns of the same name. Each operation runs in a single transaction.
    """

    def __init__(self, database: Database):
        self._database = database

    def create_tables(self, tables: Iterable[Table]) -> None:
        with self._database as db:
            for table in tables:
                logger.info(f"Applying DDL of {table.name}")
                db.execute_sql(table.ddl)

    def load_raw(self, raw_load: RawLoad, files: Iterable[tuple[str, bytes]]) -> int:
        destination = _quote_table(raw_load.destination)
        schema = _quote(raw_load.destination.split(".", 1)[0])
        columns = ", ".join(f"{_quote(column)} TEXT" for column in raw_load.columns)

        loaded = 0
        with self._database as db:
            db.execute_sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            db.execute_sql(f"DROP TABLE IF EXISTS {destination}")
            db.execute_sql(f"CREATE TABLE {destination} ({columns})")

            for path, content in files:
                if not path.lower().endswith(".csv"):
                    logger.warning(f"Only CSV files can be loaded; skipping {path}")
                    continue
                header = _csv_header(content)
                if not header:
                    logger.warning(f"Empty file; skipping {path}")
                    continue
                undeclared = [column for column in header if column not in raw_load.columns]
                if undeclared:
                    raise ValueError(f"{path} has columns {undeclared} not declared for {raw_load.destination}")

                logger.info(f"Loading {path} into {raw_load.destination}")
                loaded += db.copy_csv(raw_load.destination, header, content)

        return loaded

    def run(self, etl: Etl, pipe: Pipe) -> int:
        with self._database as db:
            if etl.pre_statement is not None:
                db.execute_sql(etl.pre_statement)

            _, columns = db.fetch_all_with_columns(f"SELECT * FROM (\n{pipe.query}\n) AS pipe LIMIT 0")
            if etl.strategy is WriteStrategy.FULL_REBUILD:
                db.execute_sql(f"DELETE FROM {_quote_table(etl.destination)}")
                rowcount = db.execute_sql(self._insert(etl, pipe, columns))
            else:
                rowcount = db.execute_sql(self._merge(etl, pipe, columns))

            if etl.post_statement is not None:
                db.execute_sql(etl.post_statement)

        return int(rowcount)

    @staticmethod
    def _insert(etl: Etl, pipe: Pipe, columns: list[str]) -> str:
        column_list = ", ".join(_quote(column) for column in columns)
        return (
            f"INSERT INTO {_quote_table(etl.destination)} ({column_list})\n"
            f"SELECT {column_list} FROM (\n{pipe.query}\n) AS pipe"
        )

    @staticmethod
    def _merge(etl: Etl, pipe: Pipe, columns: list[str]) -> str:
        missing = [column for column in etl.key if column not in columns]
        if missing:
            raise ValueError(f"ETL '{etl.name}': key columns {missing} are not produced by pipe '{pipe.name}'")

        matches = " AND ".join(f"target.{_quote(column)} = source.{_quote(column)}" for column in etl.key)
        updates = [column for column in columns if column not in etl.key]
        when_matched = (
            "UPDATE SET " + ", ".join(f"{_quote(column)} = source.{_quote(column)}" for column in updates)
            if updates else "DO NOTHING"
        )
        column_list = ", ".join(_quote(column) for column in columns)
        values = ", ".join(f"source.{_quote(column)}" for column in columns)
        return (
            f"MERGE INTO {_quote_table(etl.destination)} AS target\n"
            f"USING (\n{pipe.query}\n) AS source\n"
            f"ON {matches}\n"
            f"WHEN MATCHED THEN {when_matched}\n"
            f"WHEN NOT MATCHED THEN INSERT ({column_list}) VALUES ({values})"
        )
