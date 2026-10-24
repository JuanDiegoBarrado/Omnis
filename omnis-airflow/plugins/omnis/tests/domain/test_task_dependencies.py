import pytest

from omnis.domain import TaskDependencies


def test_orders_each_task_after_all_of_its_dependencies():
    """
    Checks: TaskDependencies (the graph.yaml of a flow) lists every task after all the tasks it
    depends on, even with several levels and several dependencies per task.

    If it fails: the topological order is wrong. Flow builds its tasks in that order, so a
    task could be built or wired before the tasks it needs, and the DAG would run an orig before
    its raw load or a clean before its orig, processing stale or empty data.
    """
    dependencies = TaskDependencies({
        "publish": ["clean"],
        "clean": ["orig_a", "orig_b"],
        "orig_a": ["raw_a"],
        "orig_b": [],
        "raw_a": [],
    })

    order = dependencies.tasks

    assert sorted(order) == ["clean", "orig_a", "orig_b", "publish", "raw_a"]
    for task in order:
        for preceding in dependencies.preceding_tasks(task):
            assert order.index(preceding) < order.index(task)


def test_roots_are_the_tasks_that_depend_on_nothing():
    """
    Checks: the roots of the graph are exactly the tasks without `after`, and preceding_tasks
    returns what a task runs after.

    If it fails: Flow wires the wrong tasks after `create_tables` (the roots) or after each
    other. A task could start before the tables exist, or before the task whose output it reads.
    """
    dependencies = TaskDependencies({"b": ["a"], "a": [], "c": []})

    assert dependencies.roots() == ["a", "c"]
    assert dependencies.preceding_tasks("b") == ("a",)


def test_a_dependency_on_an_unknown_task_fails():
    """
    Checks: a graph where a task runs `after` a task that is not in the graph is rejected.

    If it fails: a typo in graph.yaml (`after: [raw.serie_gimnasio]`) is silently accepted, and the
    task runs without waiting for the task it was meant to wait for.
    """
    with pytest.raises(ValueError, match="unknown nodes"):
        TaskDependencies({"a": ["missing"]})


def test_a_cycle_fails():
    """
    Checks: a graph with a dependency cycle (a -> c -> b -> a) is rejected when it is built.

    If it fails: a cyclic graph.yaml is not caught when the DAG file is parsed. The order would be
    incomplete or the build would loop, instead of showing a clear DAG import error.
    """
    with pytest.raises(ValueError, match="cycle"):
        TaskDependencies({"a": ["c"], "b": ["a"], "c": ["b"], "root": []})
