import pytest
from pydantic import ValidationError

from omnis.adapters import LocalDataSource, SqlPipeParser, YamlEtlGraphParser, YamlEtlParser
from omnis.domain import Etl, Pipe, RawLoad, WriteStrategy
from omnis.ports import EtlGraphRepository, EtlRepository, PipeRepository


@pytest.fixture
def source(tmp_path):
    return LocalDataSource(tmp_path)


def write(source, path, content):
    source.write(path, content.encode("utf-8"))


def etls_of(source):
    return lambda flow: EtlRepository(source, YamlEtlParser(), f"{flow}/etls")


def graphs_of(source, flow):
    return EtlGraphRepository(source, YamlEtlGraphParser(flow, etls_of(source)(flow)), flow)


def test_find_builds_the_etl_defined_in_its_file(source):
    write(source, "health/etls/orig.series_gimnasio.yaml", """
destination: orig.series_gimnasio
pipe: orig.series_gimnasio
strategy: merge
key: [fecha, num]
pre_statement: SELECT 1
""")

    etl = etls_of(source)("health").find("orig.series_gimnasio")

    assert etl == Etl(
        name="orig.series_gimnasio",
        destination="orig.series_gimnasio",
        pipe="orig.series_gimnasio",
        strategy=WriteStrategy.MERGE,
        key=("fecha", "num"),
        pre_statement="SELECT 1",
    )


def test_find_returns_none_when_there_is_no_such_artifact(source):
    assert etls_of(source)("health").find("missing") is None


def test_find_rejects_unknown_keys(source):
    write(source, "health/etls/bad.yaml", "destination: a.b\npipe: a.b\nunknown: 1\n")

    with pytest.raises(ValidationError):
        etls_of(source)("health").find("bad")


def test_find_all_only_reads_files_of_its_format_directly_under_its_folder(source):
    write(source, "health/pipes/a.sql", "SELECT 1;\n")
    write(source, "health/pipes/b.sql", "SELECT 2")
    write(source, "health/pipes/notes.md", "not a pipe")
    write(source, "health/pipes/old/c.sql", "SELECT 3")
    write(source, "health/pipes_old/d.sql", "SELECT 4")

    pipes = PipeRepository(source, SqlPipeParser(), "health/pipes").find_all()

    assert pipes == [Pipe(name="a", query="SELECT 1"), Pipe(name="b", query="SELECT 2")]


def test_graph_takes_its_flow_name_resolves_its_etl_nodes_and_builds_its_raw_loads(source):
    write(source, "health/etls/orig.x.yaml", "destination: orig.x\npipe: orig.x\n")
    write(source, "health/graph.yaml", """
nodes:
  raw.x:
    type: raw_load
    source: raw/new/x/
    destination: raw.x
    columns: [a, b]
  orig.x:
    after: [raw.x]
""")

    graph = graphs_of(source, "health").find("graph")

    assert graph.name == "health"
    assert graph.nodes == [
        RawLoad(name="raw.x", source="raw/new/x/", destination="raw.x", columns=("a", "b")),
        Etl(name="orig.x", destination="orig.x", pipe="orig.x"),
    ]
    assert graph.upstream("orig.x") == ("raw.x",)


def test_graph_fails_when_an_etl_node_has_no_definition(source):
    write(source, "health/graph.yaml", "nodes:\n  orig.x:\n")

    with pytest.raises(ValueError, match="no ETL definition"):
        graphs_of(source, "health").find("graph")
