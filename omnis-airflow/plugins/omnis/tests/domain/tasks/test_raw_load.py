import pytest

from omnis.domain import RawLoad
from omnis.tests.fakes import FakeRunner


def test_writes_and_creates_its_destination():
    """
    Checks: a raw load writes its destination and creates it itself.

    If it fails: Flow would demand DDL for the raw landing table (which must not have any), or
    would not see that the raw load is the single writer of that table.
    """
    raw_load = RawLoad("raw.t", source="raw/new/t/", destination="raw.t", columns=("a",), runner=FakeRunner())

    assert raw_load.writes == ("raw.t",)
    assert raw_load.creates == ("raw.t",)


def test_it_needs_columns():
    """
    Checks: a raw load that declares no columns is rejected.

    If it fails: the runner would try to create a table without columns, and every CSV column
    would be "not declared", so every run would fail instead of the DAG file.
    """
    with pytest.raises(ValueError, match="no columns"):
        RawLoad("raw.t", source="raw/new/t/", destination="raw.t", columns=(), runner=FakeRunner())


def test_the_file_column_cannot_be_declared():
    """
    Checks: a raw load cannot declare the column `source_file`, which the engine adds itself.

    If it fails: the declared column and the engine's would clash. The table would fail to create,
    or a CSV could fill `source_file` itself, and then the archive would move the wrong files.
    """
    with pytest.raises(ValueError, match="reserved"):
        RawLoad("raw.t", source="raw/new/t/", destination="raw.t", columns=("a", RawLoad.FILE_COLUMN), runner=FakeRunner())
