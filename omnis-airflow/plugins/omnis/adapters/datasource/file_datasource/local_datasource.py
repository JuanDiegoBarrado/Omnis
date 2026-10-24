from pathlib import Path

from omnis.ports import FileDataSource


class LocalDataSource(FileDataSource):
    """FileDataSource over a directory of the local filesystem. Paths are relative to `root`."""

    def __init__(self, root: str | Path):
        self._root = Path(root)

    def list_files(self, prefix: str) -> list[str]:
        if not self._root.exists():
            return []
        paths = (p.relative_to(self._root).as_posix() for p in self._root.rglob("*") if p.is_file())
        return sorted(p for p in paths if p.startswith(prefix))

    def exists(self, path: str) -> bool:
        return (self._root / path).is_file()

    def read_file(self, path: str) -> bytes:
        return (self._root / path).read_bytes()
