from omnis.adapters.task_runner.sql_identifiers import quote, quote_table
from omnis.domain import Etl, RunContext, WriteStrategy
from omnis.ports import Database, TaskRunner


class SqlEtlRunner(TaskRunner[Etl]):
    """
    Runs ETLs on a relational database (PostgreSQL syntax).

    The pipe of an ETL is a SELECT, embedded as a subquery: its output columns are written into the
    destination columns of the same name. Each ETL runs in a single transaction, signed with the
    run it belongs to.

    A merge only updates the rows that changed: a row whose key is already loaded is rewritten only
    if some column other than the key and the system ones differs (IS DISTINCT FROM, so a NULL
    against a value is a change). A system column of the pipe (like `sys_source_file`) is written
    with the rest when the row changes, but doesn't make it change on its own. Its row count is the
    rows inserted or changed. Comparing needs each column of the pipe to have a type the
    destination's compares with: a value that is only assignable (an integer into a TEXT column) or
    a type without equality (json) fails the merge when it is planned, before writing anything.
    """

    # Columns the warehouse keeps about a row rather than data of it (when, who, from which file)
    SYSTEM_COLUMN_PREFIX = "sys_"

    def __init__(self, database: Database):
        self._database = database

    def run(self, task: Etl, context: RunContext) -> int:
        etl = task
        with self._database as db:
            db.sign(context.blame)
            if etl.pre_statement is not None:
                db.execute_sql(etl.pre_statement)

            _, columns = db.fetch_all_with_columns(f"SELECT * FROM (\n{etl.pipe.query}\n) AS pipe LIMIT 0")
            if etl.strategy is WriteStrategy.FULL_REBUILD:
                db.execute_sql(f"DELETE FROM {quote_table(etl.destination)}")
                rowcount = db.execute_sql(self._insert(etl, columns))
            else:
                # MERGE would insert a new key returned twice, or a NULL key on every run, without failing
                invalid_keys = db.fetch_all(self._invalid_keys(etl, columns))
                if invalid_keys:
                    raise ValueError(
                        f"ETL '{etl.name}': pipe '{etl.pipe.name}' returns key values more than once or NULL,"
                        f" such as {invalid_keys} (key {list(etl.key)})"
                    )
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
    def _invalid_keys(etl: Etl, columns: list[str]) -> str:
        missing = [column for column in etl.key if column not in columns]
        if missing:
            raise ValueError(f"ETL '{etl.name}': key columns {missing} are not produced by pipe '{etl.pipe.name}'")

        key_list = ", ".join(quote(column) for column in etl.key)
        any_null = " OR ".join(f"{quote(column)} IS NULL" for column in etl.key)
        return (
            f"SELECT {key_list} FROM (\n{etl.pipe.query}\n) AS pipe\n"
            f"GROUP BY {key_list} HAVING COUNT(*) > 1 OR BOOL_OR({any_null}) LIMIT 5"
        )

    @classmethod
    def _merge(cls, etl: Etl, columns: list[str]) -> str:
        matches = " AND ".join(f"target.{quote(column)} = source.{quote(column)}" for column in etl.key)
        updates = [column for column in columns if column not in etl.key]
        compared = [column for column in updates if not column.startswith(cls.SYSTEM_COLUMN_PREFIX)]
        if compared:
            target_row = ", ".join(f"target.{quote(column)}" for column in compared)
            source_row = ", ".join(f"source.{quote(column)}" for column in compared)
            changed = f"ROW({target_row}) IS DISTINCT FROM ROW({source_row})"
            set_list = ", ".join(f"{quote(column)} = source.{quote(column)}" for column in updates)
            when_matched = f"WHEN MATCHED AND {changed} THEN UPDATE SET {set_list}"
        else:
            # Nothing but the key (and system columns) to compare: a loaded key never changes
            when_matched = "WHEN MATCHED THEN DO NOTHING"

        column_list = ", ".join(quote(column) for column in columns)
        values = ", ".join(f"source.{quote(column)}" for column in columns)
        return (
            f"MERGE INTO {quote_table(etl.destination)} AS target\n"
            f"USING (\n{etl.pipe.query}\n) AS source\n"
            f"ON {matches}\n"
            f"{when_matched}\n"
            f"WHEN NOT MATCHED THEN INSERT ({column_list}) VALUES ({values})"
        )
