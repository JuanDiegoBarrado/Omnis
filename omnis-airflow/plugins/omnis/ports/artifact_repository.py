import posixpath
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from omnis.domain import Etl, EtlGraph, Pipe, Table
from omnis.ports.data_source import DataSource

T = TypeVar("T")


class ArtifactParser(ABC, Generic[T]):
    """Builds a domain object from the content of the file that defines it."""

    extension: str

    @abstractmethod
    def parse(self, name: str, content: bytes) -> T:
        pass


class ArtifactRepository(Generic[T]):
    """
    Looks up the domain objects defined one per file directly under `prefix` of a DataSource.
    Where the files are is up to the DataSource and their format is up to the parser; the
    name of an object is its file name without extension.
    """

    def __init__(self, source: DataSource, parser: ArtifactParser[T], prefix: str):
        self._source = source
        self._parser = parser
        self._prefix = prefix.strip("/") + "/"

    def find(self, name: str) -> T | None:
        path = f"{self._prefix}{name}.{self._parser.extension}"
        if not self._source.exists(path):
            return None
        return self._parser.parse(name, self._source.read(path))

    def find_all(self) -> list[T]:
        artifacts = []
        for path in self._source.list_files(self._prefix):
            filename = path[len(self._prefix):]
            name, ext = posixpath.splitext(filename)
            if "/" in filename or ext != f".{self._parser.extension}":
                continue
            artifacts.append(self._parser.parse(name, self._source.read(path)))
        return artifacts


EtlParser = ArtifactParser[Etl]
EtlRepository = ArtifactRepository[Etl]

PipeParser = ArtifactParser[Pipe]
PipeRepository = ArtifactRepository[Pipe]

TableParser = ArtifactParser[Table]
TableRepository = ArtifactRepository[Table]

EtlGraphParser = ArtifactParser[EtlGraph]
EtlGraphRepository = ArtifactRepository[EtlGraph]
