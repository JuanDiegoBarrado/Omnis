import pytest

from omnis.domain import DDL, Flow, Table, TaskDependencies
from omnis.tests.fakes import FakeRepository, FakeRunner, FakeTask


def make_flow(graph: dict, tasks: list, tables: list | None = None, ddl_runner=None) -> Flow:
    return Flow(
        "test",
        task_dependencies_repository=FakeRepository({"graph": TaskDependencies(graph)}),
        task_repository=FakeRepository({task.name: task for task in tasks}),
        table_repository=FakeRepository({table.name: table for table in tables or []}),
        ddl_runner=ddl_runner or FakeRunner(),
    )


def test_builds_the_tasks_of_the_graph_in_its_order():
    """
    Checks: Flow takes its tasks from the task repository in the order of the graph (each after its
    dependencies), and its tables from the table repository.

    If it fails: Flow does not assemble a flow from its artifacts as declared: tasks come in the
    wrong order, or tables are lost, so their DDL would never be applied.
    """
    load = FakeTask("load", writes=("raw.a",), creates=("raw.a",))
    transform = FakeTask("transform", writes=("orig.a",))
    orig_a = Table("orig.a", "CREATE TABLE orig.a ()")

    flow = make_flow({"transform": ["load"], "load": []}, [transform, load], [orig_a])

    assert flow.tasks == [load, transform]
    assert flow.tables == [orig_a]


def test_its_ddl_task_applies_every_table_on_the_injected_runner():
    """
    Checks: the `create_tables` task of the flow holds every table of tables/ and runs on the
    ddl_runner the DAG file injected.

    If it fails: some table would not be created at the start of a run (its first writer fails
    with "relation does not exist"), or the DDL would run on a different engine than the one wired.
    """
    tables = [Table("orig.a", "DDL a"), Table("orig.b", "DDL b")]
    ddl_runner = FakeRunner()

    flow = make_flow({"t": []}, [FakeTask("t", writes=("orig.a", "orig.b"))], tables, ddl_runner)

    assert flow.ddl == DDL(tables=tuple(tables), runner=ddl_runner)
    assert flow.ddl.runner is ddl_runner


def test_a_flow_without_graph_fails():
    """
    Checks: a flow folder without graph.yaml is rejected with a LookupError.

    If it fails: a flow with its graph missing (deleted, renamed) would build an empty DAG or crash
    with an unclear error, instead of a DAG import error that says the graph is missing.
    """
    with pytest.raises(LookupError, match="no task dependencies"):
        Flow(
            "test",
            task_dependencies_repository=FakeRepository({}),
            task_repository=FakeRepository({}),
            table_repository=FakeRepository({}),
            ddl_runner=FakeRunner(),
        )


def test_a_task_of_the_graph_without_definition_fails():
    """
    Checks: a node of graph.yaml without its tasks/<node>.yaml is rejected, naming the node.

    If it fails: a node with its declaration missing (forgotten, misspelled file name) goes
    unnoticed until the flow is built, or the task silently does not exist.
    """
    with pytest.raises(ValueError, match=r"without definition \['missing'\]"):
        make_flow({"a": [], "missing": ["a"]}, [FakeTask("a")])


def test_a_task_not_in_the_graph_fails():
    """
    Checks: a tasks/<task>.yaml that is not a node of graph.yaml is rejected, naming it.

    If it fails: a declared task that was never added to the graph would silently never run, and
    the table it should write would stop being updated without anyone noticing.
    """
    with pytest.raises(ValueError, match=r"not in the graph \['extra'\]"):
        make_flow({"a": []}, [FakeTask("a"), FakeTask("extra")])


def test_no_task_can_take_the_name_of_the_ddl_task():
    """
    Checks: no declared task can be named `create_tables`, the name of the task Flow adds itself.

    If it fails: two Airflow tasks would get the same task id, and the DAG would fail to build or
    one of them would replace the other.
    """
    with pytest.raises(ValueError, match="reserved"):
        make_flow({DDL.NAME: []}, [FakeTask(DDL.NAME)])


def test_a_table_written_by_two_tasks_fails():
    """
    Checks: two tasks writing the same table are rejected (each table has a single writer).

    If it fails: two tasks could write one table, and whichever runs last would overwrite or mix
    the rows of the other: silent data loss that depends on scheduling.
    """
    tasks = [FakeTask("a", writes=("orig.t",)), FakeTask("b", writes=("orig.t",))]

    with pytest.raises(ValueError, match=r"more than one task \['orig.t'\]"):
        make_flow({"a": [], "b": []}, tasks, [Table("orig.t", "DDL")])


def test_a_table_written_without_ddl_fails():
    """
    Checks: a task that writes a table it does not create, with no DDL in tables/, is rejected.

    If it fails: the flow would build, and the task would fail on every run with "relation does
    not exist". The check moves that error to when the DAG file is parsed.
    """
    with pytest.raises(ValueError, match=r"without DDL \['orig.t'\]"):
        make_flow({"a": []}, [FakeTask("a", writes=("orig.t",))])


def test_a_table_a_task_creates_must_not_have_ddl():
    """
    Checks: a table a task creates itself on every run (a raw landing table) cannot also have DDL.

    If it fails: create_tables and the task would both define the table, and their definitions
    could disagree. The raw load drops and recreates it anyway, so the DDL would be misleading.
    """
    task = FakeTask("load", writes=("raw.t",), creates=("raw.t",))

    with pytest.raises(ValueError, match=r"must not have DDL \['raw.t'\]"):
        make_flow({"load": []}, [task], [Table("raw.t", "DDL")])


def test_builds_the_dag_wired_as_the_graph_after_the_ddl_task():
    """
    Checks: the Airflow DAG has the flow name as dag_id, the tags plus `omnis`, `create_tables`
    first, the roots right after it and every other task after the tasks of its `after`.

    If it fails: the DAG Airflow runs does not match graph.yaml. Tasks could run in parallel when
    they should wait, or before the tables are created.
    """
    tasks = [FakeTask("a"), FakeTask("b"), FakeTask("c")]
    flow = make_flow({"a": [], "b": [], "c": ["a", "b"]}, tasks)

    dag = flow.build_airflow_dag(schedule=None, tags=["health"])

    assert dag.dag_id == "test"
    assert set(dag.tags) == {"omnis", "health"}
    assert set(dag.task_dict) == {DDL.NAME, "a", "b", "c"}
    assert dag.task_dict[DDL.NAME].downstream_task_ids == {"a", "b"}
    assert dag.task_dict["c"].upstream_task_ids == {"a", "b"}


def test_the_dag_does_not_catch_up_unless_asked():
    """
    Checks: the DAG is built with catchup=False unless the DAG file asks for catchup.

    If it fails: enabling a DAG would launch one run per missed schedule since its start date, all
    loading and merging the same raw files at once.
    """
    flow = make_flow({"a": []}, [FakeTask("a")])

    assert flow.build_airflow_dag(schedule=None).catchup is False
    assert flow.build_airflow_dag(schedule=None, catchup=True).catchup is True
