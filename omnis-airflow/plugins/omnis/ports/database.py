from abc import ABC, abstractmethod


class Database(ABC):
    """
    Port to talk to a database without knowing its driver: any driver/engine change stays
    localized to an adapter.

    Implementations are used as context managers: entering opens a connection and starts a
    transaction, exiting commits on success or rolls back on error.
    """

    @abstractmethod
    def __enter__(self) -> "Database":
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    @abstractmethod
    def execute_sql(self, query: str, params=None) -> int:
        """Execute a statement and return the number of affected rows."""
        pass

    @abstractmethod
    def fetch_all(self, query: str, params=None) -> list[tuple]:
        """Execute a query and return every row."""
        pass

    @abstractmethod
    def fetch_all_with_columns(self, query: str, params=None) -> tuple[list[tuple], list[str]]:
        """Execute a query and return every row plus the resulting column names."""
        pass

    @abstractmethod
    def copy_csv(self, table_name: str, columns: list[str], content: bytes) -> int:
        """Bulk load CSV content (UTF-8, with a header line) into `columns` of a table. Returns the rows loaded."""
        pass
