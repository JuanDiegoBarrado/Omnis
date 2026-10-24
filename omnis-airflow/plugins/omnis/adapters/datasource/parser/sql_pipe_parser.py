from omnis.domain import Pipe
from omnis.ports import Parser


class SqlPipeParser(Parser[Pipe]):
    """Pipes written as a single SQL SELECT per file."""

    format = "sql"

    def parse(self, name: str, content: bytes) -> Pipe:
        # The query is embedded as a subquery, so a trailing ';' must go
        query = content.decode("utf-8-sig").strip().rstrip(";").rstrip()
        return Pipe(name=name, query=query)
