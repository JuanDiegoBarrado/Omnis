import pytest

from omnis.domain import Etl, Pipe, WriteStrategy
from omnis.tests.fakes import FakeRunner

PIPE = Pipe("orig.t", "SELECT 1 AS id")


def test_writes_its_destination():
    """
    Checks: an ETL writes its destination and creates no table, and is a full rebuild by default.

    If it fails: Flow's checks rely on `writes` and `creates`. The single writer and "has DDL"
    checks would miss this ETL's destination, and an ETL declared without strategy could merge.
    """
    etl = Etl("orig.t", destination="orig.t", pipe=PIPE, runner=FakeRunner())

    assert etl.writes == ("orig.t",)
    assert etl.creates == ()
    assert etl.strategy is WriteStrategy.FULL_REBUILD


def test_a_merge_needs_a_key():
    """
    Checks: a merge ETL without key columns is rejected.

    If it fails: a merge would have nothing to match rows on, so the runner would build an invalid
    MERGE that fails on every run instead of failing when the DAG file is parsed.
    """
    with pytest.raises(ValueError, match="needs the key"):
        Etl("orig.t", destination="orig.t", pipe=PIPE, strategy=WriteStrategy.MERGE, runner=FakeRunner())


def test_a_full_rebuild_does_not_take_a_key():
    """
    Checks: a full rebuild ETL with key columns is rejected.

    If it fails: someone who meant `strategy: merge` but forgot it would get a full rebuild, which
    deletes the destination's history on every run, believing that rows are kept by key.
    """
    with pytest.raises(ValueError, match="does not use a key"):
        Etl("orig.t", destination="orig.t", pipe=PIPE, key=("id",), runner=FakeRunner())


def test_a_pipe_cannot_be_empty():
    """
    Checks: a pipe whose query is blank is rejected.

    If it fails: an empty .sql file in artifacts/pipes/ would reach the runner, which would fail
    with a SQL syntax error on every run instead of when the DAG file is parsed.
    """
    with pytest.raises(ValueError, match="empty"):
        Pipe("orig.t", "  \n")
