"""Test doubles of the ports, for the tests that must not depend on any adapter."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from omnis.domain import Task
from omnis.ports import FileDataSource, Parser, TaskRunner


class FakeRunner(TaskRunner[Any]):
    """Records the tasks it runs and returns `result`."""

    def __init__(self, result: int = 0):
        self.result = result
        self.runs: list[Task] = []

    def run(self, task: Any) -> int:
        self.runs.append(task)
        return self.result


@dataclass(frozen=True)
class FakeTask(Task):
    """A task that writes and creates the tables it is told to."""

    name: str
    writes: tuple[str, ...] = ()
    creates: tuple[str, ...] = ()
    runner: TaskRunner[Any] = field(default_factory=FakeRunner, kw_only=True, compare=False, repr=False)


class InMemoryFiles(FileDataSource):
    """FileDataSource over a dict of path -> content."""

    def __init__(self, files: dict[str, bytes] | None = None):
        self.files = dict(files or {})

    def list_files(self, prefix: str) -> list[str]:
        return sorted(path for path in self.files if path.startswith(prefix))

    def exists(self, path: str) -> bool:
        return path in self.files

    def read_file(self, path: str) -> bytes:
        return self.files[path]

    def move_file(self, path: str, new_path: str) -> None:
        self.files[new_path] = self.files.pop(path)


class FakeParser(Parser[str]):
    """Parses the content as text. Fails with ValueError on content that is `invalid`."""

    format = "txt"

    def parse(self, name: str, content: bytes) -> str:
        text = content.decode()
        if text == "invalid":
            raise ValueError("invalid content")
        return text


class FakeRepository:
    """Stands in for any repository: returns the objects it holds, by name."""

    def __init__(self, items: dict[str, Any]):
        self.items = items

    def query_names(self) -> list[str]:
        return list(self.items)

    def find(self, name: str = "graph") -> Any:
        return self.items.get(name)

    def find_all(self, names: list[str]) -> list[Any]:
        return [self.items[name] for name in names]
