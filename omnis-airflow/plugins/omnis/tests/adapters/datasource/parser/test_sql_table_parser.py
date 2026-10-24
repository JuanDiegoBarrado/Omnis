from omnis.adapters import SqlTableParser
from omnis.domain import Table


def test_the_ddl_is_the_whole_script():
    """
    Checks: a table file is read as its whole script, every statement in it, without the UTF-8 BOM.

    If it fails: part of a table's DDL would be lost (the CREATE SCHEMA, an index, a function), or
    the BOM would reach Postgres and make create_tables fail.
    """
    content = "﻿CREATE SCHEMA IF NOT EXISTS orig;\nCREATE TABLE IF NOT EXISTS orig.t (a INT);\n".encode("utf-8")

    assert SqlTableParser().parse("orig.t", content) == Table(
        "orig.t", "CREATE SCHEMA IF NOT EXISTS orig;\nCREATE TABLE IF NOT EXISTS orig.t (a INT);\n"
    )
