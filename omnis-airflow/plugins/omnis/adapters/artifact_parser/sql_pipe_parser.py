from omnis.domain import Pipe
from omnis.ports import PipeParser


class SqlPipeParser(PipeParser):
    """Pipes written as a single SQL SELECT per file."""

    extension = "sql"

    def parse(self, name: str, content: bytes) -> Pipe:
        # The query is embedded as a subquery, so a trailing ';' must go
        query = content.decode("utf-8-sig").strip().rstrip(";").rstrip()
        return Pipe(name=name, query=query)
