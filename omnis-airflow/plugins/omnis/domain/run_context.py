from dataclasses import dataclass


@dataclass(frozen=True)
class RunContext:
    """
    The run of a flow a task runs in: Airflow's DAG run, named by the flow and its run id. A
    runner signs what it writes with its `blame`, so every row says which run wrote it.
    """

    flow: str
    run_id: str

    @property
    def blame(self) -> str:
        """What a runner signs its writes with: `<flow>/<run_id>`."""
        return f"{self.flow}/{self.run_id}"
