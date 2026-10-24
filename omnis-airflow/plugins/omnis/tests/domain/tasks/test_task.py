from airflow.sdk import DAG

from omnis.tests.fakes import FakeRunner, FakeTask


def test_its_airflow_task_runs_it_on_its_runner():
    """
    Checks: the Airflow task that Task.build_task adds is named after the task and, when Airflow
    runs it, calls the task's runner with the task itself and returns what the runner returns.

    If it fails: the bridge between the engine and Airflow is broken. Airflow would run nothing,
    run another task, or run the task on the wrong runner, whatever the flow declares.
    """
    runner = FakeRunner(result=42)
    task = FakeTask("load", runner=runner)

    with DAG("test", schedule=None) as dag:
        task.build_task()
    operator = dag.task_dict["load"]

    assert operator.python_callable() == 42
    assert runner.runs == [task]
