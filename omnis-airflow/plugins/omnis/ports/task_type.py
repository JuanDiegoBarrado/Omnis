from abc import ABC, abstractmethod

from omnis.domain import Task


class TaskType(ABC):
    """
    How the declaration of one type of task becomes its domain Task: it validates what the
    declaration says, resolves what it references (the pipe of an ETL) and gives the task its
    runner. It knows nothing about the format the declaration was written in.
    """

    # The value of `type` in the declarations of this type of task
    name: str

    @abstractmethod
    def build(self, name: str, declaration: dict) -> Task:
        """The task `name` its declaration describes. Raises ValueError if the declaration is not valid."""
