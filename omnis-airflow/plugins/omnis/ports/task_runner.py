from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class TaskRunner(ABC, Generic[T]):
    """
    Port to run one type of task (T) wherever its implementation does: a database, a cluster...
    Each task carries its runner, so the tasks of a flow can run on different engines.
    """

    @abstractmethod
    def run(self, task: T) -> int:
        """Do the work of `task`. Returns how much it did (rows written, tables applied...)."""
