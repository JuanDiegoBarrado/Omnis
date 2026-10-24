from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

from airflow.sdk import task

if TYPE_CHECKING:
    from airflow.sdk.definitions.xcom_arg import XComArg

    from omnis.ports import TaskRunner


class Task(ABC):
    """A step of a flow, run as one Airflow task named after it on the runner it carries."""

    name: str
    runner: TaskRunner[Any]

    @property
    def writes(self) -> tuple[str, ...]:
        """The tables this task writes. Each table of a flow has a single writer."""
        return ()

    @property
    def creates(self) -> tuple[str, ...]:
        """
        The tables among `writes` that this task creates itself on every run, so they must not
        have DDL. Every other table it writes must have its DDL in the flow.
        """
        return ()

    @property
    def doc(self) -> str:
        """What this task does, shown in Airflow as the documentation of its task."""
        return ""

    def build_task(self) -> XComArg:
        """Add the Airflow task that runs this task on its runner to the DAG being defined, and return it."""

        @task(task_id=self.name, doc_md=self.doc or None)
        def run():
            return self.runner.run(self)

        return run()
