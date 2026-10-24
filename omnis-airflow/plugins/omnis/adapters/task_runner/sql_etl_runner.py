from omnis.adapters.task_runner.sql_identifiers import quote, quote_table
from omnis.domain import Etl, WriteStrategy
from omnis.ports import Database, TaskRunner


class SqlEtlRunner(TaskRunner[Etl]):
    """
    Runs ETLs on a relational database (PostgreSQL syntax).

    The pipe of an ETL is a SELECT, embedded as a subquery: its output columns are written into the
    destination columns of the same name. Each ETL runs in a single transaction.
    """

    def __init__(self, database: Database):
        self._database = database

    def run(self, task: Etl) -> int:
        etl = task
        with self._database as db:
            if etl.pre_statement is not None:
                db.execute_sql(etl.pre_statement)

            _, columns = db.fetch_all_with_columns(f"SELECT * FROM (\n{etl.pipe.query}\n) AS pipe LIMIT 0")
            if etl.strategy is WriteStrategy.FULL_REBUILD:
                db.execute_sql(f"DELETE FROM {quote_table(etl.destination)}")
                rowcount = db.execute_sql(self._insert(etl, columns))
            else:
                rowcount = db.execute_sql(self._merge(etl, columns))

            if etl.post_statement is not None:
                db.execute_sql(etl.post_statement)

        return int(rowcount)

    @staticmethod
    def _insert(etl: Etl, columns: list[str]) -> str:
        column_list = ", ".join(quote(column) for column in columns)
        return (
            f"INSERT INTO {quote_table(etl.destination)} ({column_list})\n"
            f"SELECT {column_list} FROM (\n{etl.pipe.query}\n) AS pipe"
        )

    @staticmethod
    def _merge(etl: Etl, columns: list[str]) -> str:
        missing = [column for column in etl.key if column not in columns]
        if missing:
            raise ValueError(f"ETL '{etl.name}': key columns {missing} are not produced by pipe '{etl.pipe.name}'")

        matches = " AND ".join(f"target.{quote(column)} = source.{quote(column)}" for column in etl.key)
        updates = [column for column in columns if column not in etl.key]
        when_matched = (
            "UPDATE SET " + ", ".join(f"{quote(column)} = source.{quote(column)}" for column in updates)
            if updates else "DO NOTHING"
        )
        column_list = ", ".join(quote(column) for column in columns)
        values = ", ".join(f"source.{quote(column)}" for column in columns)
        return (
            f"MERGE INTO {quote_table(etl.destination)} AS target\n"
            f"USING (\n{etl.pipe.query}\n) AS source\n"
            f"ON {matches}\n"
            f"WHEN MATCHED THEN {when_matched}\n"
            f"WHEN NOT MATCHED THEN INSERT ({column_list}) VALUES ({values})"
        )
