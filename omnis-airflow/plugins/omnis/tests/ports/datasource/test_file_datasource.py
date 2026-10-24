"""What FileDataSource builds on the file operations of each storage (see test_file_datasource_contract for those)."""
from omnis.tests.fakes import InMemoryFiles


def test_names_are_the_files_of_the_format_directly_under_the_location():
    """
    Checks: the names under a location are the files with that extension directly in that folder:
    not other extensions, not files in subfolders, not other folders sharing the prefix, and
    whether the location has leading or trailing slashes.

    If it fails: the raw load would pick up files it must not (a .txt, an old/ subfolder,
    raw/new/t_backup/), or miss the CSVs it must load. Repositories would see artifacts that
    aren't there or lose some.
    """
    files = InMemoryFiles({
        "raw/new/t/a.csv": b"",
        "raw/new/t/b.csv": b"",
        "raw/new/t/notes.txt": b"",
        "raw/new/t/old/c.csv": b"",
        "raw/new/other/d.csv": b"",
    })

    assert files.query_names("raw/new/t", "csv") == ["a", "b"]
    assert files.query_names("/raw/new/t/", "csv") == ["a", "b"]


def test_an_empty_location_is_the_root():
    """
    Checks: an empty location means the root folder: its files, not those of its subfolders.

    If it fails: graph.yaml, which lives at the root of the flow folder, would not be found, or
    every tasks/*.yaml would be taken as a graph.
    """
    files = InMemoryFiles({"graph.yaml": b"", "tasks/a.yaml": b""})

    assert files.query_names("", "yaml") == ["graph"]
    assert files.describe("", "graph", "yaml") == "graph.yaml"


def test_reads_the_file_of_a_name_or_none():
    """
    Checks: reading a name returns the content of <location>/<name>.<format>, or None when there
    is no such file.

    If it fails: repositories could not tell a missing artifact (None, which Flow reports by name)
    from an error, or would read the wrong file.
    """
    files = InMemoryFiles({"tables/t.sql": b"DDL"})

    assert files.read("tables", "t", "sql") == b"DDL"
    assert files.read("tables", "missing", "sql") is None


def test_moves_the_file_of_a_name_to_another_location():
    """
    Checks: moving a name takes its file to the same name in the other location and leaves the
    other files alone.

    If it fails: the archive would put files in the wrong place, rename them, or touch files it was
    not asked to move.
    """
    files = InMemoryFiles({"raw/new/t/a.csv": b"rows", "raw/new/t/b.csv": b"other"})

    assert files.move("raw/new/t/", "a", "csv", "raw/his/t/") is True
    assert files.files == {"raw/his/t/a.csv": b"rows", "raw/new/t/b.csv": b"other"}


def test_moving_a_name_that_is_not_there_moves_nothing():
    """
    Checks: moving a name with no file returns False and changes nothing.

    If it fails: retrying an archive that already moved some files would crash on the first one it
    can't find, so a half-done archive could never be completed.
    """
    files = InMemoryFiles({"raw/new/t/a.csv": b"rows"})

    assert files.move("raw/new/t/", "missing", "csv", "raw/his/t/") is False
    assert files.files == {"raw/new/t/a.csv": b"rows"}
