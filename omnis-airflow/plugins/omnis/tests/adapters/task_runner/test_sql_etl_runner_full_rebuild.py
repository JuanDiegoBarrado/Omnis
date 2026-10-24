"""
A full rebuild ETL on each case of its folder: the tables in given/, the rebuild, the tables in
expected/. The tables and the pipe are the same for every case.
"""
from pathlib import Path

import pytest

from omnis.adapters import PostgresDatabase, SqlEtlRunner
from omnis.domain import Etl, Pipe

pytestmark = pytest.mark.integration

DATA = Path(__file__).with_suffix("")
CASES = sorted(path for path in DATA.iterdir() if path.is_dir())


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_full_rebuild(postgres, case):
    """
    Checks: a full rebuild leaves its destination with exactly the rows of its pipe, as the clean
    and publish tables are rebuilt on every run. Each case (its folder name is the test id):
      - replaces_the_whole_content: rows the pipe no longer returns disappear, and the rest are
        the pipe's.
      - empty_origin_empties_the_destination: if the pipe returns nothing, the destination ends up
        empty. That is what "rebuild" means, so a full rebuild must never read from a table that
        only holds the latest files (a raw table).

    If it fails: clean/publish tables would keep stale rows next to the new ones (counted twice in
    the reports), or not reflect what their origin holds.
    """
    postgres.execute((DATA / "tables.sql").read_text(encoding="utf-8"))
    postgres.load(case / "given")
    etl = Etl(
        "dst.destination",
        destination="dst.destination",
        pipe=Pipe("dst.destination", (DATA / "pipe.sql").read_text(encoding="utf-8")),
        runner=SqlEtlRunner(PostgresDatabase(postgres.dsn)),
    )

    etl.runner.run(etl)

    postgres.assert_tables(case / "expected")
