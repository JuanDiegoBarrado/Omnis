import pytest

from omnis.domain import Etl, EtlGraph, RawLoad, WriteStrategy


def etl(name, destination=None):
    return Etl(name=name, destination=destination or name, pipe=name)


def raw(name):
    return RawLoad(name=name, source=f"raw/new/{name}/", destination=name, columns=("a",))


def test_nodes_come_after_their_dependencies():
    graph = EtlGraph(
        "health",
        [etl("publish.x"), etl("clean.x"), etl("orig.x"), raw("raw.x")],
        {"orig.x": ["raw.x"], "clean.x": ["orig.x"], "publish.x": ["clean.x"]},
    )

    assert [node.name for node in graph.nodes] == ["raw.x", "orig.x", "clean.x", "publish.x"]
    assert graph.roots() == ["raw.x"]
    assert graph.upstream("clean.x") == ("orig.x",)


def test_rejects_dependencies_on_unknown_nodes():
    with pytest.raises(ValueError, match="unknown nodes"):
        EtlGraph("health", [etl("orig.x")], {"orig.x": ["raw.x"]})


def test_rejects_cycles():
    with pytest.raises(ValueError, match="cycle"):
        EtlGraph("health", [etl("a"), etl("b")], {"a": ["b"], "b": ["a"]})


def test_rejects_two_producers_for_the_same_table():
    with pytest.raises(ValueError, match="more than one node"):
        EtlGraph("health", [etl("a", "clean.x"), etl("b", "clean.x")], {})


def test_merge_needs_a_key_and_full_rebuild_does_not_use_one():
    with pytest.raises(ValueError, match="key"):
        Etl(name="orig.x", destination="orig.x", pipe="orig.x", strategy=WriteStrategy.MERGE)
    with pytest.raises(ValueError, match="key"):
        Etl(name="orig.x", destination="orig.x", pipe="orig.x", key=("id",))
