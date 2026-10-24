from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from omnis.domain.tasks.task import Task

if TYPE_CHECKING:
    from omnis.ports import TaskRunner


@dataclass(frozen=True)
class Pipe:
    """
    The processing itself: a query that produces rows from tables, with its origins written
    inside it. It does not know where its rows are written (that is the ETL's job).
    """

    name: str
    query: str

    def __post_init__(self):
        if not self.query.strip():
            raise ValueError(f"Pipe '{self.name}' is empty")


class WriteStrategy(Enum):
    """How an ETL writes the rows of its pipe into its destination."""

    FULL_REBUILD = "full_rebuild"   # replace the whole content of the destination
    MERGE = "merge"                 # update the rows whose key already exists, insert the rest


@dataclass(frozen=True)
class Etl(Task):
    """
    Writes the rows produced by its pipe into a destination table ('schema.table').

    `pre_statement` and `post_statement` are optional hooks run right before and after
    writing, in the same transaction. A MERGE needs the `key` columns that identify a row.
    """

    name: str
    destination: str
    pipe: Pipe
    strategy: WriteStrategy = WriteStrategy.FULL_REBUILD
    key: tuple[str, ...] = ()
    pre_statement: str | None = None
    post_statement: str | None = None
    runner: TaskRunner[Etl] = field(kw_only=True, compare=False, repr=False)

    def __post_init__(self):
        if self.strategy is WriteStrategy.MERGE and not self.key:
            raise ValueError(f"ETL '{self.name}': a merge needs the key columns that identify a row")
        if self.strategy is WriteStrategy.FULL_REBUILD and self.key:
            raise ValueError(f"ETL '{self.name}': a full rebuild does not use a key")

    @property
    def writes(self) -> tuple[str, ...]:
        return (self.destination,)

    @property
    def doc(self) -> str:
        return (
            f"ETL into `{self.destination}` ({self.strategy.value}"
            + (f", key {', '.join(self.key)}" if self.key else "")
            + f") with pipe `{self.pipe.name}`:\n\n```sql\n{self.pipe.query}\n```"
        )
