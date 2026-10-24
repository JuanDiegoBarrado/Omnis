from abc import ABC, abstractmethod


class Notifier(ABC):
    """Port to tell someone that a run of a flow failed, through whatever channel its implementation uses."""

    @abstractmethod
    def notify_failure(self, flow: str, run_id: str, reason: str, last_task: str | None) -> None:
        """
        Tell that the run `run_id` of `flow` failed, and why as the orchestrator reports it.
        `last_task` is the last task that finished, when the orchestrator knows it: not always the
        one that failed.
        """
