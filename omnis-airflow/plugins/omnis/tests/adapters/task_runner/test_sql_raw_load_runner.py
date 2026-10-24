"""
Raw loads of the CSV files in files/ of each folder of its data, checked against expected/. The
files are read from the local filesystem: reading them from S3 is the contract of the storages.
"""
import shutil
from pathlib import Path

import pytest

from omnis.adapters import LocalDataSource, PostgresDatabase, SqlRawLoadRunner
from omnis.domain import RawLoad

pytestmark = pytest.mark.integration

DATA = Path(__file__).with_suffix("")


def drop_files(case: str, root: Path) -> None:
    """Copy the files of `case` into the source of the raw load under `root`, as a producer would."""
    shutil.copytree(DATA / case / "files", root / "files", dirs_exist_ok=True, copy_function=shutil.copyfile)


def remove_files(root: Path) -> None:
    for path in (root / "files").iterdir():
        path.unlink()


def make_raw_load(postgres, root: Path) -> RawLoad:
    return RawLoad(
        "raw.series",
        source="files/",
        destination="raw.series",
        columns=("fecha", "num", "ejercicio", "peso"),
        runner=SqlRawLoadRunner(PostgresDatabase(postgres.dsn), raw_files=LocalDataSource(root)),
    )


def test_lands_every_csv_directly_under_the_source_matching_columns_by_header(postgres):
    """
    Checks: the CSVs a producer may drop (producer_formats/files/) are landed as text, each row
    with the name of its file in `source_file`:
      - a file with every column, and values with quoted commas and placeholders ('-');
      - a file with only some of the columns, in another order, with a header in other case and
        with spaces and a BOM: its missing columns are NULL;
      - a header-only file and an empty file add no rows; a .txt and a file in a subfolder are ignored.

    If it fails: producers' files would land in the wrong columns, lose rows, or be read from where
    they shouldn't. Without the right `source_file`, the archive would move files that weren't loaded.
    """
    raw_load = make_raw_load(postgres, DATA / "producer_formats")

    loaded = raw_load.runner.run(raw_load)

    assert loaded == 3
    postgres.assert_tables(DATA / "producer_formats" / "expected")


def test_without_files_it_leaves_its_table_empty(postgres, tmp_path):
    """
    Checks: a run with no files in the source (nothing new arrived) succeeds, loads 0 rows and
    leaves the raw table empty, with all its columns.

    If it fails: a day without new files would fail the whole DAG, or leave no raw table for the
    orig pipes that read it.
    """
    raw_load = make_raw_load(postgres, tmp_path)

    assert raw_load.runner.run(raw_load) == 0
    postgres.assert_tables(DATA / "empty" / "expected")


def test_replaces_what_the_previous_run_loaded(postgres, tmp_path):
    """
    Checks: each run replaces the raw table with only the files that are in the source now. The
    rows of a file that was archived since the previous run disappear.

    If it fails: the raw table would accumulate the files of every run, so orig would process them
    all again each time, and a full rebuild reading from raw would count them more than once.
    """
    raw_load = make_raw_load(postgres, tmp_path)
    drop_files("first_run", tmp_path)
    raw_load.runner.run(raw_load)

    remove_files(tmp_path)
    drop_files("second_run", tmp_path)
    raw_load.runner.run(raw_load)

    postgres.assert_tables(DATA / "second_run" / "expected")


def test_a_file_with_an_undeclared_column_fails_and_keeps_the_previous_load(postgres, tmp_path):
    """
    Checks: a file with a column the raw load doesn't declare fails the load, naming the column, and
    the raw table keeps what the previous run loaded (the DROP and CREATE are undone too).

    If it fails: a producer adding a column would have it silently dropped, or the failed load would
    leave the raw table deleted or half loaded.
    """
    raw_load = make_raw_load(postgres, tmp_path)
    drop_files("first_run", tmp_path)
    raw_load.runner.run(raw_load)

    drop_files("undeclared_column", tmp_path)
    with pytest.raises(ValueError, match=r"columns \['unknown'\] not declared"):
        raw_load.runner.run(raw_load)

    postgres.assert_tables(DATA / "first_run" / "expected")
