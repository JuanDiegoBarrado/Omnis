from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from omnis.domain.tasks.task import Task

if TYPE_CHECKING:
    from omnis.ports import TaskRunner


@dataclass(frozen=True)
class Archive(Task):
    """
    Moves the raw files a raw load landed from its `source` to `destination`, so the next runs
    don't load them again.

    The files to move are the ones named in RawLoad.FILE_COLUMN of `files_from`, the destination
    of that raw load, so a file that arrives after the load is left for the next run. The graph
    must run it after the tasks that process `files_from`: it only runs if they succeed.
    """

    name: str
    files_from: str
    source: str
    destination: str
    runner: TaskRunner[Archive] = field(kw_only=True, compare=False, repr=False)

    def __post_init__(self):
        if self.source.strip("/") == self.destination.strip("/"):
            raise ValueError(f"Archive '{self.name}': source and destination are the same")

    @property
    def doc(self) -> str:
        return f"Move the files loaded into `{self.files_from}` from `{self.source}` to `{self.destination}`."
