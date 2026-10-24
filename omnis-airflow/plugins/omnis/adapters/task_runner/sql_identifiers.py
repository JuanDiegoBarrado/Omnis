"""Quoting of identifiers in the SQL the runners write (PostgreSQL syntax)."""


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def quote_table(table: str) -> str:
    """A 'schema.table' name, each part quoted."""
    return ".".join(quote(part) for part in table.split(".", 1))
