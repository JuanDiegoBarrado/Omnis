from typing import ClassVar, Generic, TypeVar

from omnis.ports.datasource.datasource import DataSource
from omnis.ports.datasource.parser import Parser

T = TypeVar("T")


class Repository(Generic[T]):
    """
    The artifacts of one kind of one flow, looked up by name: read from `source` and built by
    `parser`. A flow chooses where its artifacts are kept and in which format; where they are
    within the flow (`location`) is the plugin's convention, fixed by the subclass of each kind.
    Errors are prefixed with where the artifact is (DataSource.describe).
    """

    location: ClassVar[str]

    def __init__(self, source: DataSource, parser: Parser[T]):
        self.source = source
        self.parser = parser

    def query_names(self) -> list[str]:
        """The names of the artifacts, without building them."""
        return self.source.query_names(self.location, self.parser.format)

    def find(self, name: str) -> T | None:
        """The artifact `name`, built, or None when the flow has no such artifact."""
        content = self.source.read(self.location, name, self.parser.format)
        if content is None:
            return None
        try:
            return self.parser.parse(name, content)
        except ValueError as error:
            raise ValueError(f"{self.source.describe(self.location, name, self.parser.format)}: {error}") from error

    def find_all(self, names: list[str]) -> list[T]:
        """The artifacts `names`, built and in that order. Raises LookupError if any of them does not exist."""
        artifacts = [self.find(name) for name in names]
        missing = [name for name, artifact in zip(names, artifacts) if artifact is None]
        if missing:
            raise LookupError(f"Not found in '{self.location or './'}': {missing}")
        return [artifact for artifact in artifacts if artifact is not None]
