from omnis.domain import Task
from omnis.ports.repository.repository import Repository


class TaskRepository(Repository[Task]):
    """
    The tasks of one flow, declared under tasks/. Its parser builds them with the artifacts they
    reference (the pipe of an ETL) and the runner they run on, so the flow works with tasks and
    never with the declarations behind them.
    """

    location = "tasks"
