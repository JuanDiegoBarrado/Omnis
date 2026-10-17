from dataclasses import dataclass


@dataclass(frozen=True)
class RawLoad:
    """
    Lands raw files into a database table so ETLs can process them.

    Every run replaces the destination with the content of the files found under `source`.
    The destination is a text-only table with the declared `columns`; files may carry any
    subset of them, matched by their header.
    """

    name: str
    source: str
    destination: str
    columns: tuple[str, ...]

    def __post_init__(self):
        if not self.columns:
            raise ValueError(f"Raw load '{self.name}' declares no columns")
