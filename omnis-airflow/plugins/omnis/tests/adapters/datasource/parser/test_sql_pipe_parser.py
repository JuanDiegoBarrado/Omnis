from omnis.adapters import SqlPipeParser
from omnis.domain import Pipe


def test_the_query_loses_its_trailing_semicolon_to_be_embedded():
    """
    Checks: a pipe file is read as its query without the UTF-8 BOM, the surrounding blank space or
    the trailing `;`, keeping its comments.

    If it fails: the runner embeds the query as a subquery (`SELECT * FROM (<pipe>)`), so a trailing
    `;` or a BOM left in it would make every ETL whose pipe has them fail with a syntax error.
    """
    content = "﻿-- comment\nSELECT a\nFROM t ;\n\n".encode("utf-8")

    assert SqlPipeParser().parse("orig.t", content) == Pipe("orig.t", "-- comment\nSELECT a\nFROM t")
