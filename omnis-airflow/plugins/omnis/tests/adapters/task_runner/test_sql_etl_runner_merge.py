"""
A merge ETL on each case of its folder: the tables in given/, the merge by `id`, the tables in
expected/. The tables and the pipe are the same for every case: like an orig table, the destination
keeps in `sys_source_file` the file of the last change of each row, which the pipe takes from the
`source_file` of its origin.
"""
from pathlib import Path

import pytest

from omnis.adapters import PostgresDatabase, SqlEtlRunner
from omnis.domain import Etl, Pipe, WriteStrategy
from omnis.tests.fakes import RUN_CONTEXT

pytestmark = pytest.mark.integration

DATA = Path(__file__).with_suffix("")
CASES = sorted(path for path in DATA.iterdir() if path.is_dir())


def load(postgres, case: Path) -> None:
    postgres.execute((DATA / "tables.sql").read_text(encoding="utf-8"))
    postgres.load(case / "given")


def merge(postgres) -> int:
    etl = Etl(
        "dst.destination",
        destination="dst.destination",
        pipe=Pipe("dst.destination", (DATA / "pipe.sql").read_text(encoding="utf-8")),
        strategy=WriteStrategy.MERGE,
        key=("id",),
        runner=SqlEtlRunner(PostgresDatabase(postgres.dsn)),
    )
    return etl.runner.run(etl, RUN_CONTEXT)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_merge(postgres, case):
    """
    Checks: a merge by key writes the pipe's rows into a destination that already has rows, as the
    orig tables do on every run. Each case (its folder name is the test id) checks one rule:
      - new_equal_and_modified: a new key is inserted, an equal row stays as it was and a row with
        a known key and other values replaces the loaded one, with the file it now comes from.
      - same_values_in_another_file: a row that arrives again with the same values, in another
        file, keeps the file it was first loaded from: a system column alone is not a change.
      - keeps_rows_the_pipe_does_not_return: rows of the destination whose key the pipe doesn't
        return (files already archived) stay untouched.
      - a_null_replaces_a_value: a NULL from the pipe replaces the loaded value (a NULL against a
        value is a change, although `NULL <> 80` is not true in SQL).
      - empty_origin: with nothing to merge (no new files), the destination doesn't change.

    If it fails: the MERGE the runner builds is wrong. orig would duplicate rows, ignore corrections,
    point to a file that didn't change the row, or lose the history of files that are no longer in
    raw/new. Raw files are archived after each run, so orig is the only place that keeps that history.
    """
    load(postgres, case)

    merge(postgres)

    postgres.assert_tables(case / "expected")


def test_rewrites_only_the_rows_that_change(postgres):
    """
    Checks: on the case new_equal_and_modified, the merge counts 2 rows (the new one and the
    modified one), and the row that came back equal is not rewritten: its xmin (the transaction
    that wrote its current version) stays the same, while the modified row gets a new one.

    If it fails: every run would rewrite each row the pipe returns, even when nothing changed (a
    file loaded again, a retried run). The warehouse would record those rows as modified by that
    run (their sys_fec_mod and sys_blame), so it could no longer tell when or by whom a row really
    changed, and the task would report rows it didn't change.
    """
    load(postgres, DATA / "new_equal_and_modified")
    before = dict(postgres.fetch("SELECT id, xmin::text FROM dst.destination"))

    assert merge(postgres) == 2

    after = dict(postgres.fetch("SELECT id, xmin::text FROM dst.destination"))
    assert after[1] == before[1]
    assert after[2] != before[2]
