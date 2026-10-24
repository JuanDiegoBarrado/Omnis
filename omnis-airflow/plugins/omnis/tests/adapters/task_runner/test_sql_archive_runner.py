"""
Archives of files on the local filesystem (moving them on S3 is the contract of the storages).
Only the names of the files matter, so their content is a placeholder.
"""
from pathlib import Path

import pytest

from omnis.adapters import LocalDataSource, PostgresDatabase, SqlArchiveRunner, SqlRawLoadRunner
from omnis.domain import Archive, RawLoad

pytestmark = pytest.mark.integration


def files_under(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def drop(root: Path, *names: str) -> None:
    for name in names:
        path = root / "raw/new/t" / f"{name}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"a\n1\n")


def make_archive(postgres, root: Path) -> Archive:
    return Archive(
        "archive.t",
        files_from="raw.t",
        source="raw/new/t/",
        destination="raw/his/t/",
        runner=SqlArchiveRunner(PostgresDatabase(postgres.dsn), raw_files=LocalDataSource(root)),
    )


@pytest.fixture
def postgres(postgres):
    postgres.execute(f"CREATE SCHEMA raw; CREATE TABLE raw.t (a TEXT, {RawLoad.FILE_COLUMN} TEXT)")
    return postgres


def test_moves_only_the_files_named_in_its_table(postgres, tmp_path):
    """
    Checks: the archive moves to raw/his exactly the files named in `source_file` of the raw table
    (each once, even if it has several rows) and leaves any other file of raw/new where it is.

    If it fails: files that were never loaded would be archived. Their rows would never reach orig,
    and nothing would warn about it: data lost unless someone moves them back by hand.
    """
    drop(tmp_path, "a", "b", "c")
    postgres.execute("INSERT INTO raw.t VALUES ('1', 'a'), ('2', 'a'), ('3', 'b'), ('4', NULL)")
    archive = make_archive(postgres, tmp_path)

    assert archive.runner.run(archive) == 2
    assert files_under(tmp_path) == ["raw/his/t/a.csv", "raw/his/t/b.csv", "raw/new/t/c.csv"]


def test_a_file_already_moved_is_skipped_so_it_can_be_retried(postgres, tmp_path):
    """
    Checks: a file named in the table that is no longer in raw/new is skipped without failing, so
    running the archive again after a partial failure completes it.

    If it fails: an archive that failed halfway (a network error with S3) could never be completed.
    It would fail on the first file it already moved, while the rest stay in raw/new.
    """
    drop(tmp_path, "b")
    postgres.execute("INSERT INTO raw.t VALUES ('1', 'a'), ('2', 'b')")
    archive = make_archive(postgres, tmp_path)

    assert archive.runner.run(archive) == 1
    assert archive.runner.run(archive) == 0
    assert files_under(tmp_path) == ["raw/his/t/b.csv"]


def test_with_its_table_empty_it_moves_nothing(postgres, tmp_path):
    """
    Checks: if the raw load landed nothing (an empty raw table), the archive moves nothing.

    If it fails: a run without new data could move files that are in raw/new but were never loaded.
    """
    drop(tmp_path, "a")
    archive = make_archive(postgres, tmp_path)

    assert archive.runner.run(archive) == 0
    assert files_under(tmp_path) == ["raw/new/t/a.csv"]


def test_a_file_dropped_after_the_raw_load_waits_for_the_next_run(postgres, tmp_path):
    """
    Checks: with a real raw load and archive, a file a producer drops between the two (while orig
    runs) stays in raw/new for the next run, and the loaded one is archived.

    If it fails: the archive and the raw load disagree on which files were loaded, so a file that
    arrives mid-run would be archived without being loaded, and silently lost from orig.
    """
    raw_load = RawLoad(
        "raw.t",
        source="raw/new/t/",
        destination="raw.t",
        columns=("a",),
        runner=SqlRawLoadRunner(PostgresDatabase(postgres.dsn), raw_files=LocalDataSource(tmp_path)),
    )
    archive = make_archive(postgres, tmp_path)
    drop(tmp_path, "loaded")

    raw_load.runner.run(raw_load)
    drop(tmp_path, "late")
    archive.runner.run(archive)

    assert files_under(tmp_path) == ["raw/his/t/loaded.csv", "raw/new/t/late.csv"]
