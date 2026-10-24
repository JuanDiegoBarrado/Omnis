from typing import Literal

from pydantic import BaseModel, ConfigDict

from omnis.domain import Archive
from omnis.ports import TaskRunner, TaskType


class ArchiveDeclaration(BaseModel):
    """
    What the declaration of an archive task says (`type: archive`): moves the files loaded into
    the table `files_from` from `source` to `destination`.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["archive"]
    files_from: str
    source: str
    destination: str


class ArchiveTaskType(TaskType):
    """Archive tasks (see ArchiveDeclaration)."""

    name = "archive"

    def __init__(self, runner: TaskRunner[Archive]):
        self.runner = runner

    def build(self, name: str, declaration: dict) -> Archive:
        spec = ArchiveDeclaration.model_validate(declaration)
        return Archive(
            name=name,
            files_from=spec.files_from,
            source=spec.source,
            destination=spec.destination,
            runner=self.runner,
        )
