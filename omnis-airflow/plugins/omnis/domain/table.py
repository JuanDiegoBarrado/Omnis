from dataclasses import dataclass


@dataclass(frozen=True)
class Table:
    """The definition (DDL) of a database object a flow needs. Applying it must be idempotent."""

    name: str
    ddl: str
