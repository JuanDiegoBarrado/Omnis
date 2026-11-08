from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

from airflow.sdk import task

from omnis.domain.run_context import RunContext

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
        """
        Add the Airflow task that runs this task on its runner to the DAG being defined, and return it.
        The runner is told the run it runs in (the DAG id, which is the flow name, and the run id),
        so it can sign what it writes.
        """

        @task(task_id=self.name, doc_md=self.doc or None)
        def run(**context):
            # Airflow passes its context to a task function that takes **kwargs
            return self.runner.run(self, RunContext(flow=context["dag"].dag_id, run_id=context["run_id"]))

        return run()
