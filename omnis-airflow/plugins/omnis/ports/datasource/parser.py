from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Parser(ABC, Generic[T]):
    """Builds an object from the bytes it is written in."""

    # The format it reads ("yaml", "sql"...), which a DataSource may need to find what is written in it
    format: str

    @abstractmethod
    def parse(self, name: str, content: bytes) -> T:
        pass
