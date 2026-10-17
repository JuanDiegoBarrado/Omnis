from abc import ABC, abstractmethod


class DataSource(ABC):
    """
    Where files live (S3/MinIO, local filesystem...). Works with raw bytes and
    '/'-separated paths, knowing nothing about the format of the files.
    """

    @abstractmethod
    def list_files(self, prefix: str) -> list[str]:
        """Return the path of every file under `prefix`."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass

    @abstractmethod
    def read(self, path: str) -> bytes:
        pass

    @abstractmethod
    def write(self, path: str, content: bytes) -> None:
        pass

    @abstractmethod
    def move(self, source: str, destination: str) -> None:
        pass
