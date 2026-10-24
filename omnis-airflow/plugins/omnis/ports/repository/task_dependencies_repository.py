from omnis.domain import TaskDependencies
from omnis.ports.repository.repository import Repository


class TaskDependenciesRepository(Repository[TaskDependencies]):
    """Which task of one flow precedes which: the graph at the root of the flow."""

    location = ""

    # Every flow names its graph the same
    NAME = "graph"

    def find(self, name: str = NAME) -> TaskDependencies | None:
        """The task dependencies of the flow, or None when it has none."""
        return super().find(name)
