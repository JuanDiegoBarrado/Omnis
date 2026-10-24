import pytest
from pydantic import ValidationError

from omnis.adapters import EtlTaskType, SqlPipeParser
from omnis.domain import Etl, Pipe, WriteStrategy
from omnis.ports import PipeRepository
from omnis.tests.fakes import FakeRunner, InMemoryFiles

PIPES = InMemoryFiles({"artifacts/pipes/orig.t.sql": b"SELECT a, b FROM raw.t"})


def make_task_type(runner=None) -> EtlTaskType:
    return EtlTaskType(pipe_repository=PipeRepository(PIPES, SqlPipeParser()), runner=runner or FakeRunner())


def test_builds_the_etl_with_its_pipe_and_runner():
    """
    Checks: an `etl` declaration with every key becomes an Etl with the pipe it names (read from
    artifacts/pipes/), its strategy, key, statements and the runner the flow injected.

    If it fails: ETLs would be built with settings other than those declared: the wrong pipe, a
    merge as a full rebuild (losing history), hooks that never run, or the wrong runner.
    """
    runner = FakeRunner()
    declaration = {
        "type": "etl",
        "destination": "orig.t",
        "pipe": "orig.t",
        "strategy": "merge",
        "key": ["a"],
        "pre_statement": "SELECT 1",
        "post_statement": "SELECT 2",
    }

    etl = make_task_type(runner).build("orig.t", declaration)

    assert etl == Etl(
        "orig.t",
        destination="orig.t",
        pipe=Pipe("orig.t", "SELECT a, b FROM raw.t"),
        strategy=WriteStrategy.MERGE,
        key=("a",),
        pre_statement="SELECT 1",
        post_statement="SELECT 2",
        runner=runner,
    )
    assert etl.runner is runner


def test_an_etl_is_a_full_rebuild_unless_declared():
    """
    Checks: an ETL declared without `strategy` is a full rebuild with no key.

    If it fails: the documented default changed. The clean and publish ETLs, which don't declare a
    strategy, would stop rebuilding their tables (or fail for lack of key).
    """
    etl = make_task_type().build("orig.t", {"type": "etl", "destination": "orig.t", "pipe": "orig.t"})

    assert etl.strategy is WriteStrategy.FULL_REBUILD
    assert etl.key == ()


def test_a_pipe_that_does_not_exist_fails():
    """
    Checks: an ETL whose `pipe` names a file not in artifacts/pipes/ is rejected, naming the pipe.

    If it fails: a misspelled or deleted pipe would be found out only when the ETL runs, or the
    ETL would be built without a query.
    """
    with pytest.raises(ValueError, match="pipe 'missing' not found"):
        make_task_type().build("orig.t", {"type": "etl", "destination": "orig.t", "pipe": "missing"})


@pytest.mark.parametrize("declaration", [
    {"type": "etl", "destination": "orig.t"},
    {"type": "etl", "destination": "orig.t", "pipe": "orig.t", "strategy": "append"},
    {"type": "etl", "destination": "orig.t", "pipe": "orig.t", "columns": ["a"]},
])
def test_an_invalid_declaration_fails(declaration):
    """
    Checks: an ETL declaration without `pipe`, with an unknown strategy or with a key it doesn't
    take is rejected.

    If it fails: mistakes in tasks/*.yaml would be ignored: an unknown key would silently do
    nothing, and a misspelled strategy could fall back to the default (a full rebuild that deletes
    the history).
    """
    with pytest.raises(ValidationError):
        make_task_type().build("orig.t", declaration)
