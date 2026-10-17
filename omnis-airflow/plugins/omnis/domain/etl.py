from dataclasses import dataclass
from enum import Enum


class WriteStrategy(Enum):
    """How an ETL writes the rows of its pipe into its destination."""

    FULL_REBUILD = "full_rebuild"   # replace the whole content of the destination
    MERGE = "merge"                 # update the rows whose key already exists, insert the rest


@dataclass(frozen=True)
class Etl:
    """
    Writes the rows produced by a pipe into a destination table ('schema.table').

    The pipe is referenced by name. `pre_statement` and `post_statement` are optional hooks
    run right before and after writing, in the same transaction. A MERGE needs the `key`
    columns that identify a row.
    """

    name: str
    destination: str
    pipe: str
    strategy: WriteStrategy = WriteStrategy.FULL_REBUILD
    key: tuple[str, ...] = ()
    pre_statement: str | None = None
    post_statement: str | None = None

    def __post_init__(self):
        if self.strategy is WriteStrategy.MERGE and not self.key:
            raise ValueError(f"ETL '{self.name}': a merge needs the key columns that identify a row")
        if self.strategy is WriteStrategy.FULL_REBUILD and self.key:
            raise ValueError(f"ETL '{self.name}': a full rebuild does not use a key")
