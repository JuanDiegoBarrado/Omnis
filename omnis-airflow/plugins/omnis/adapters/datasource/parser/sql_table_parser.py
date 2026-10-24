from omnis.domain import Table
from omnis.ports import Parser


class SqlTableParser(Parser[Table]):
    """Tables written as SQL DDL scripts."""

    format = "sql"

    def parse(self, name: str, content: bytes) -> Table:
        return Table(name=name, ddl=content.decode("utf-8-sig"))
