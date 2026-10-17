from abc import ABC, abstractmethod
from collections.abc import Iterable

from omnis.domain import Etl, Pipe, RawLoad, Table


class EtlExecutor(ABC):
    """
    Port to run the work of a flow on the warehouse without knowing the engine underneath:
    create its tables, land raw files and execute ETLs.
    """

    @abstractmethod
    def create_tables(self, tables: Iterable[Table]) -> None:
        """Apply the DDL of every table. Tables that already exist are left as they are."""
        pass

    @abstractmethod
    def load_raw(self, raw_load: RawLoad, files: Iterable[tuple[str, bytes]]) -> int:
        """Replace the destination of `raw_load` with the content of `files` (path, content). Returns the rows loaded."""
        pass

    @abstractmethod
    def run(self, etl: Etl, pipe: Pipe) -> int:
        """Write the rows of `pipe` into the destination of `etl` with its strategy. Returns the rows written."""
        pass
