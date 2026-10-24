"""
A merge ETL on each case of its folder: the tables in given/, the merge by `id`, the tables in
expected/. The tables and the pipe are the same for every case.
"""
from pathlib import Path

import pytest

from omnis.adapters import PostgresDatabase, SqlEtlRunner
from omnis.domain import Etl, Pipe, WriteStrategy

pytestmark = pytest.mark.integration

DATA = Path(__file__).with_suffix("")
CASES = sorted(path for path in DATA.iterdir() if path.is_dir())


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_merge(postgres, case):
    """
    Checks: a merge by key writes the pipe's rows into a destination that already has rows, as the
    orig tables do on every run. Each case (its folder name is the test id) checks one rule:
      - new_equal_and_modified: a new key is inserted, an equal row stays as it was and a row with
        a known key and other values replaces the loaded one.
      - keeps_rows_the_pipe_does_not_return: rows of the destination whose key the pipe doesn't
        return (files already archived) stay untouched.
      - a_null_replaces_a_value: a NULL from the pipe replaces the loaded value.
      - empty_origin: with nothing to merge (no new files), the destination doesn't change.

    If it fails: the MERGE the runner builds is wrong. orig would duplicate rows, ignore corrections,
    or lose the history of files that are no longer in raw/new. Raw files are archived after each
    run, so orig is the only place that keeps that history.
    """
    postgres.execute((DATA / "tables.sql").read_text(encoding="utf-8"))
    postgres.load(case / "given")
    etl = Etl(
        "dst.destination",
        destination="dst.destination",
        pipe=Pipe("dst.destination", (DATA / "pipe.sql").read_text(encoding="utf-8")),
        strategy=WriteStrategy.MERGE,
        key=("id",),
        runner=SqlEtlRunner(PostgresDatabase(postgres.dsn)),
    )

    etl.runner.run(etl)

    postgres.assert_tables(case / "expected")
