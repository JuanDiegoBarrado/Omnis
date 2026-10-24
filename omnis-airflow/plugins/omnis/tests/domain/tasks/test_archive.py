import pytest

from omnis.domain import Archive
from omnis.tests.fakes import FakeRunner


def test_writes_no_table():
    """
    Checks: an archive writes and creates no table (it only moves files).

    If it fails: Flow would treat the archive as a writer of a table: it would demand DDL for it,
    or report the raw table as written by two tasks, and every flow with an archive would break.
    """
    archive = Archive("archive.t", files_from="raw.t", source="raw/new/t/", destination="raw/his/t/", runner=FakeRunner())

    assert archive.writes == ()
    assert archive.creates == ()


def test_source_and_destination_cannot_be_the_same():
    """
    Checks: an archive whose destination is its own source is rejected, whatever the slashes.

    If it fails: the archive would move each file onto itself. Nothing would leave raw/new, so
    every run would load every file again, while the archive reports the files as archived.
    """
    with pytest.raises(ValueError, match="the same"):
        Archive("archive.t", files_from="raw.t", source="raw/new/t/", destination="/raw/new/t", runner=FakeRunner())
