from abc import ABC, abstractmethod


class DataSource(ABC):
    """
    Where data lives (files of S3/MinIO or the local filesystem, a database...): the contents
    kept under a `location`, looked up by name. Works with raw bytes, knowing nothing about
    their format; `format` is only what a source may need to find them (a file extension).
    """

    @abstractmethod
    def query_names(self, location: str, format: str) -> list[str]:
        """The names of what is kept under `location` in `format`, without reading it."""

    @abstractmethod
    def read(self, location: str, name: str, format: str) -> bytes | None:
        """The content of `name`, or None when there is no such content under `location`."""

    @abstractmethod
    def describe(self, location: str, name: str, format: str) -> str:
        """Where `name` is kept, as the error messages show it (a file path...)."""

    @abstractmethod
    def move(self, location: str, name: str, format: str, to_location: str) -> bool:
        """
        Move `name` from `location` to `to_location`, replacing what is there with that name.
        Returns False, moving nothing, when there is no such content under `location`.
        """
