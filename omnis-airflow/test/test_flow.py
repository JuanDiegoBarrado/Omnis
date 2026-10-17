import pytest

from omnis.domain import Etl, EtlGraph, Flow, Pipe, RawLoad, Table


def graph():
    return EtlGraph(
        "health",
        [
            RawLoad(name="raw.x", source="raw/new/x/", destination="raw.x", columns=("a",)),
            Etl(name="orig.x", destination="orig.x", pipe="orig.x"),
        ],
        {"orig.x": ["raw.x"]},
    )


def test_gives_the_pipe_of_each_etl():
    pipe = Pipe(name="orig.x", query="SELECT a FROM raw.x")

    flow = Flow(graph(), [pipe, Pipe(name="unused", query="SELECT 1")], [Table(name="orig.x", ddl="...")])

    assert flow.name == "health"
    assert flow.pipe_of(flow.graph.node("orig.x")) == pipe


def test_rejects_an_etl_without_its_pipe():
    with pytest.raises(ValueError, match="pipes"):
        Flow(graph(), [], [Table(name="orig.x", ddl="...")])


def test_rejects_an_etl_destination_without_ddl():
    with pytest.raises(ValueError, match="without DDL"):
        Flow(graph(), [Pipe(name="orig.x", query="SELECT a FROM raw.x")], [])


def test_rejects_ddl_for_a_raw_landing_table():
    tables = [Table(name="orig.x", ddl="..."), Table(name="raw.x", ddl="...")]
    with pytest.raises(ValueError, match="raw landing tables"):
        Flow(graph(), [Pipe(name="orig.x", query="SELECT a FROM raw.x")], tables)
