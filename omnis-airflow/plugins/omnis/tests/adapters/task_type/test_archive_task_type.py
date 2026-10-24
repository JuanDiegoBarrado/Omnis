import pytest
from pydantic import ValidationError

from omnis.adapters import ArchiveTaskType
from omnis.domain import Archive
from omnis.tests.fakes import FakeRunner


def test_builds_the_archive_with_its_runner():
    """
    Checks: an `archive` declaration becomes an Archive with its files_from table, source,
    destination and the runner the flow injected.

    If it fails: archives would read the file names from another table or move files between other
    prefixes than those declared, archiving files that were never loaded.
    """
    runner = FakeRunner()
    declaration = {"type": "archive", "files_from": "raw.t", "source": "raw/new/t/", "destination": "raw/his/t/"}

    archive = ArchiveTaskType(runner).build("archive.t", declaration)

    assert archive == Archive("archive.t", files_from="raw.t", source="raw/new/t/", destination="raw/his/t/", runner=runner)
    assert archive.runner is runner


@pytest.mark.parametrize("declaration", [
    {"type": "archive", "source": "raw/new/t/", "destination": "raw/his/t/"},
    {"type": "archive", "files_from": "raw.t", "source": "raw/new/t/", "destination": "raw/his/t/", "columns": ["a"]},
])
def test_an_invalid_declaration_fails(declaration):
    """
    Checks: an archive declaration without `files_from`, or with a key it doesn't take, is rejected.

    If it fails: an archive would not know which table lists the loaded files. Mistakes in its
    YAML would be ignored when the DAG file is parsed.
    """
    with pytest.raises(ValidationError):
        ArchiveTaskType(FakeRunner()).build("archive.t", declaration)
