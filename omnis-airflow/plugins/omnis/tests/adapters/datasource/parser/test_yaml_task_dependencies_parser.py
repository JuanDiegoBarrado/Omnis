from pathlib import Path

import pytest
from pydantic import ValidationError

from omnis.adapters import YamlTaskDependenciesParser

DATA = Path(__file__).with_suffix("")


def parse(file: str):
    return YamlTaskDependenciesParser().parse("graph", (DATA / file).read_bytes())


def test_reads_which_task_runs_after_which():
    """
    Checks: a graph.yaml (the one in the folder of this module) is read with its nodes and their
    `after`, whether a root is written as a bare key or with an empty `after`.

    If it fails: the flows' graph.yaml would be misread. Tasks would lose their dependencies (and
    run too early) or bare keys would be rejected, and every DAG would fail to import.
    """
    dependencies = parse("graph.yaml")

    assert dependencies.roots() == ["raw.a", "raw.b"]
    assert dependencies.preceding_tasks("orig.a") == ("raw.a",)
    assert dependencies.preceding_tasks("clean.ab") == ("orig.a", "raw.b")


def test_a_node_takes_no_key_but_after():
    """
    Checks: a node with any key other than `after` (node_with_unknown_key.yaml has a `type`)
    is rejected.

    If it fails: task settings written in graph.yaml by mistake would be silently ignored, and the
    person who wrote them would believe they apply.
    """
    with pytest.raises(ValidationError, match="type"):
        parse("node_with_unknown_key.yaml")
