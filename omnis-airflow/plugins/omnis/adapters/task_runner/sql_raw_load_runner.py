import csv
import logging

from omnis.adapters.task_runner.sql_identifiers import quote, quote_table
from omnis.domain import RawLoad
from omnis.ports import Database, DataSource, TaskRunner

logger = logging.getLogger(__name__)


def _csv_header(content: bytes) -> list[str]:
    first_line = content.decode("utf-8-sig").splitlines()[:1]
    header = next(csv.reader(first_line), [])
    return [column.strip().lower() for column in header]


class SqlRawLoadRunner(TaskRunner[RawLoad]):
    """
    Lands the CSV files of a raw load into a relational database (PostgreSQL syntax), reading
    them from `raw_files`: every CSV under its `source`. Each load runs in a single transaction.
    """

    def __init__(self, database: Database, raw_files: DataSource):
        self._database = database
        self._raw_files = raw_files

    def run(self, task: RawLoad) -> int:
        raw_load = task
        destination = quote_table(raw_load.destination)
        schema = quote(raw_load.destination.split(".", 1)[0])
        columns = ", ".join(f"{quote(column)} TEXT" for column in raw_load.columns)

        loaded = 0
        with self._database as db:
            db.execute_sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            db.execute_sql(f"DROP TABLE IF EXISTS {destination}")
            db.execute_sql(f"CREATE TABLE {destination} ({columns})")

            for name in self._raw_files.query_names(raw_load.source, "csv"):
                path = self._raw_files.describe(raw_load.source, name, "csv")
                content = self._raw_files.read(raw_load.source, name, "csv") or b""
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
