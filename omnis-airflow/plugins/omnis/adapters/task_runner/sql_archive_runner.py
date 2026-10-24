import logging

from omnis.adapters.task_runner.sql_identifiers import quote, quote_table
from omnis.domain import Archive, RawLoad
from omnis.ports import Database, DataSource, TaskRunner

logger = logging.getLogger(__name__)


class SqlArchiveRunner(TaskRunner[Archive]):
    """
    Moves the CSV files of `raw_files` named in the raw load table of an archive (PostgreSQL
    syntax). A file that is no longer in its source (already moved by an earlier try) is skipped,
    so a failed archive can be retried.
    """

    def __init__(self, database: Database, raw_files: DataSource):
        self._database = database
        self._raw_files = raw_files

    def run(self, task: Archive) -> int:
        archive = task
        file_column = quote(RawLoad.FILE_COLUMN)
        with self._database as db:
            rows = db.fetch_all(
                f"SELECT DISTINCT {file_column} FROM {quote_table(archive.files_from)} "
                f"WHERE {file_column} IS NOT NULL ORDER BY {file_column}"
            )

        moved = 0
        for (name,) in rows:
            path = self._raw_files.describe(archive.source, name, "csv")
            if self._raw_files.move(archive.source, name, "csv", archive.destination):
                logger.info(f"Moved {path} to {archive.destination}")
                moved += 1
            else:
                logger.warning(f"Not in the source (already moved?); skipping {path}")
        return moved
