import logging

from omnis.domain import DDL
from omnis.ports import Database, TaskRunner

logger = logging.getLogger(__name__)


class SqlDdlRunner(TaskRunner[DDL]):
    """Applies the DDL of the tables of a flow on a relational database, in a single transaction."""

    def __init__(self, database: Database):
        self._database = database

    def run(self, task: DDL) -> int:
        with self._database as db:
            for table in task.tables:
                logger.info(f"Applying DDL of {table.name}")
                db.execute_sql(table.ddl)
        return len(task.tables)
