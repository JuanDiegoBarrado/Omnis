from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from omnis.domain import RunContext

T = TypeVar("T")


class TaskRunner(ABC, Generic[T]):
    """
    Port to run one type of task (T) wherever its implementation does: a database, a cluster...
    Each task carries its runner, so the tasks of a flow can run on different engines.
    """

    @abstractmethod
    def run(self, task: T, context: RunContext) -> int:
        """
        Do the work of `task` in the run `context`. A runner that writes traced data signs it with
        `context.blame`. Returns how much it did (rows written, tables applied...).
        """
