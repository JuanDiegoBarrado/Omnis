import shutil
from pathlib import Path

from omnis.ports import DataSource


class LocalDataSource(DataSource):
    """DataSource over a directory of the local filesystem. Paths are relative to `root`."""

    def __init__(self, root: str | Path):
        self._root = Path(root)

    def list_files(self, prefix: str) -> list[str]:
        if not self._root.exists():
            return []
        paths = (p.relative_to(self._root).as_posix() for p in self._root.rglob("*") if p.is_file())
        return sorted(p for p in paths if p.startswith(prefix))

    def exists(self, path: str) -> bool:
        return (self._root / path).is_file()

    def read(self, path: str) -> bytes:
        return (self._root / path).read_bytes()

    def write(self, path: str, content: bytes) -> None:
        target = self._root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    def move(self, source: str, destination: str) -> None:
        target = self._root / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(self._root / source, target)
