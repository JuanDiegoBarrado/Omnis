from dataclasses import dataclass


@dataclass(frozen=True)
class Pipe:
    """
    The processing itself: a query that produces rows from tables, with its origins written
    inside it. It does not know where its rows are written (that is the ETL's job).
    """

    name: str
    query: str

    def __post_init__(self):
        if not self.query.strip():
            raise ValueError(f"Pipe '{self.name}' is empty")
