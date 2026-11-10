from pathlib import Path

from omnis.ports import FileDataSource


class LocalDataSource(FileDataSource):
    """FileDataSource over a directory of the local filesystem. Paths are relative to `root`."""

    def __init__(self, root: str | Path):
        self._root = Path(root)

    def list_files(self, prefix: str) -> list[str]:
        # Only the folder the prefix is in is walked, not the whole root: in the landing zone that
        # would be every file ever archived (raw/his), on every raw load
        start = self._root / prefix.rpartition("/")[0]
        if not start.is_dir():
            return []
        paths = (p.relative_to(self._root).as_posix() for p in start.rglob("*") if p.is_file())
        return sorted(p for p in paths if p.startswith(prefix))

    def exists(self, path: str) -> bool:
        return (self._root / path).is_file()

    def read_file(self, path: str) -> bytes:
        return (self._root / path).read_bytes()

    def move_file(self, path: str, new_path: str) -> None:
        target = self._root / new_path
        target.parent.mkdir(parents=True, exist_ok=True)
        (self._root / path).replace(target)
