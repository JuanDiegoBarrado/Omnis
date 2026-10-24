from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from omnis.domain.tasks.task import Task

if TYPE_CHECKING:
    from omnis.ports import TaskRunner


@dataclass(frozen=True)
class RawLoad(Task):
    """
    Lands raw files into a database table so ETLs can process them.

    Every run replaces the destination with the content of the raw files found under `source`.
    The destination is a text-only table with the declared `columns`, which the load creates
    itself; files may carry any subset of them, matched by their header.
    """

    name: str
    source: str
    destination: str
    columns: tuple[str, ...]
    runner: TaskRunner[RawLoad] = field(kw_only=True, compare=False, repr=False)

    def __post_init__(self):
        if not self.columns:
            raise ValueError(f"Raw load '{self.name}' declares no columns")

    @property
    def writes(self) -> tuple[str, ...]:
        return (self.destination,)

    @property
    def creates(self) -> tuple[str, ...]:
        return (self.destination,)

    @property
    def doc(self) -> str:
        return f"Raw load of the files under `{self.source}` into `{self.destination}`."
