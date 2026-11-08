from airflow.sdk import DAG

from omnis.domain import RunContext
from omnis.tests.fakes import FakeRunner, FakeTask


def test_its_airflow_task_runs_it_on_its_runner():
    """
    Checks: the Airflow task that Task.build_task adds is named after the task and, when Airflow
    runs it (with the run's context: the DAG and the run id), calls the task's runner with the task
    itself and the run it belongs to (the DAG id, which is the flow name, and the run id), and
    returns what the runner returns.

    If it fails: the bridge between the engine and Airflow is broken. Airflow would run nothing,
    run another task, or run the task on the wrong runner, whatever the flow declares. Or the
    runner wouldn't know its run, and the rows it writes would not say which run wrote them.
    """
    runner = FakeRunner(result=42)
    task = FakeTask("load", runner=runner)

    with DAG("health", schedule=None) as dag:
        task.build_task()
    operator = dag.task_dict["load"]

    assert operator.python_callable(dag=dag, run_id="manual__1") == 42
    assert runner.runs == [task]
    assert runner.contexts == [RunContext("health", "manual__1")]
