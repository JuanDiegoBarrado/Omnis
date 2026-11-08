import logging

from omnis.domain import DDL, RunContext
from omnis.ports import Database, TaskRunner

logger = logging.getLogger(__name__)


class SqlDdlRunner(TaskRunner[DDL]):
    """
    Applies the DDL of the tables of a flow on a relational database, in a single transaction.
    It is signed with the run it belongs to, since a DDL may also write rows (a reference table
    that replaces its rows on every run).
    """

    def __init__(self, database: Database):
        self._database = database

    def run(self, task: DDL, context: RunContext) -> int:
        with self._database as db:
            db.sign(context.blame)
            for table in task.tables:
                logger.info(f"Applying DDL of {table.name}")
                db.execute_sql(table.ddl)
        return len(task.tables)
