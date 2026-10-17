from omnis.domain import Table
from omnis.ports import TableParser


class SqlTableParser(TableParser):
    """Tables written as SQL DDL scripts."""

    extension = "sql"

    def parse(self, name: str, content: bytes) -> Table:
        return Table(name=name, ddl=content.decode("utf-8-sig"))
