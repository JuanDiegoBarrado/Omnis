from omnis.domain import Table
from omnis.ports.repository.repository import Repository


class TableRepository(Repository[Table]):
    """The tables one flow creates with its DDL, under tables/."""

    location = "tables"
