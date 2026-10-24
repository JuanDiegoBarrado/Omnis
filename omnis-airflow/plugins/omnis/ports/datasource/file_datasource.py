import posixpath
from abc import abstractmethod

from omnis.ports.datasource.datasource import DataSource


class FileDataSource(DataSource):
    """
    Data kept one per file, `<location>/<name>.<format>` with '/'-separated paths (`location` is
    a folder, the root when empty). Files in subfolders of a location are not under it.
    Each implementation only says how to list and read files (S3/MinIO, local filesystem...).
    """

    @abstractmethod
    def list_files(self, prefix: str) -> list[str]:
        """Return the path of every file under `prefix`."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass

    @abstractmethod
    def read_file(self, path: str) -> bytes:
        pass

    def query_names(self, location: str, format: str) -> list[str]:
        prefix = _prefix(location)
        names = []
        for path in self.list_files(prefix):
            filename = path[len(prefix):]
            name, ext = posixpath.splitext(filename)
            if "/" not in filename and ext == f".{format}":
                names.append(name)
        return names

    def read(self, location: str, name: str, format: str) -> bytes | None:
        path = self.describe(location, name, format)
        if not self.exists(path):
            return None
        return self.read_file(path)

    def describe(self, location: str, name: str, format: str) -> str:
        """The path of the file of `name`."""
        return f"{_prefix(location)}{name}.{format}"


def _prefix(location: str) -> str:
    location = location.strip("/")
    return f"{location}/" if location else ""
