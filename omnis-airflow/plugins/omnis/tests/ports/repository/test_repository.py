import pytest

from omnis.ports import PipeRepository, Repository, TableRepository, TaskDependenciesRepository, TaskRepository
from omnis.tests.fakes import FakeParser, InMemoryFiles


class NotesRepository(Repository[str]):
    location = "notes"


def make_repository(files: dict[str, bytes]) -> NotesRepository:
    return NotesRepository(InMemoryFiles(files), FakeParser())


def test_names_are_the_artifacts_in_its_location_and_format():
    """
    Checks: a repository's names are the files of its parser's format in its own location only.

    If it fails: Flow would see tasks, pipes or tables that don't exist (from another folder or
    format) or miss real ones, and its graph/tasks check would fail or pass wrongly.
    """
    repository = make_repository({"notes/a.txt": b"A", "notes/b.txt": b"B", "notes/c.yaml": b"", "other/d.txt": b""})

    assert repository.query_names() == ["a", "b"]


def test_finds_an_artifact_built_by_its_parser_or_none():
    """
    Checks: finding a name reads it from the source and builds it with the parser, or returns None
    when it does not exist.

    If it fails: artifacts would come back unbuilt, or a missing artifact would raise instead of
    None, so the callers' clear "not found" errors would never show.
    """
    repository = make_repository({"notes/a.txt": b"A"})

    assert repository.find("a") == "A"
    assert repository.find("missing") is None


def test_a_parse_error_says_where_the_artifact_is():
    """
    Checks: an error while building an artifact starts with the path of its file.

    If it fails: a wrong YAML or SQL file would break the DAG with a message that doesn't say which
    of the flow's files is wrong.
    """
    repository = make_repository({"notes/a.txt": b"invalid"})

    with pytest.raises(ValueError, match=r"^notes/a\.txt: invalid content"):
        repository.find("a")


def test_finds_several_artifacts_in_the_order_asked():
    """
    Checks: finding several names returns them built, in the order they were asked for.

    If it fails: Flow asks for its tasks in the graph's order, so tasks would come back out of
    order (or mismatched with their names).
    """
    repository = make_repository({"notes/a.txt": b"A", "notes/b.txt": b"B"})

    assert repository.find_all(["b", "a"]) == ["B", "A"]


def test_finding_several_fails_if_any_is_missing():
    """
    Checks: finding several names fails with LookupError naming the missing ones.

    If it fails: a missing artifact would be silently dropped, and a flow would run without one of
    its tasks or tables.
    """
    repository = make_repository({"notes/a.txt": b"A"})

    with pytest.raises(LookupError, match=r"\['missing'\]"):
        repository.find_all(["a", "missing"])


@pytest.mark.parametrize(("repository", "location"), [
    (TaskDependenciesRepository, ""),
    (TaskRepository, "tasks"),
    (PipeRepository, "artifacts/pipes"),
    (TableRepository, "tables"),
])
def test_where_each_kind_of_artifact_is_within_a_flow(repository, location):
    """
    Checks: where each kind of artifact lives inside a flow folder (graph at the root, tasks/,
    artifacts/pipes/, tables/), the layout every flow is written in.

    If it fails: someone changed the layout of the flow folders. Every existing flow would stop
    finding its artifacts until its folders are moved to match.
    """
    assert repository.location == location


def test_the_graph_is_found_by_its_fixed_name():
    """
    Checks: the graph of a flow is found without giving a name, because every flow calls it `graph`.

    If it fails: Flow, which calls find() without a name, would not find any flow's graph.yaml, and
    every DAG would fail to import.
    """
    repository = TaskDependenciesRepository(InMemoryFiles({"graph.txt": b"G"}), FakeParser())

    assert repository.find() == "G"
