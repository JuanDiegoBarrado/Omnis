from typing import Literal

from pydantic import BaseModel, ConfigDict

from omnis.domain import RawLoad
from omnis.ports import TaskRunner, TaskType


class RawLoadDeclaration(BaseModel):
    """What the declaration of a raw load task says (`type: raw_load`): lands the files under `source` into `destination`."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["raw_load"]
    source: str
    destination: str
    columns: list[str]


class RawLoadTaskType(TaskType):
    """Raw load tasks (see RawLoadDeclaration)."""

    name = "raw_load"

    def __init__(self, runner: TaskRunner[RawLoad]):
        self.runner = runner

    def build(self, name: str, declaration: dict) -> RawLoad:
        spec = RawLoadDeclaration.model_validate(declaration)
        return RawLoad(
            name=name,
            source=spec.source,
            destination=spec.destination,
            columns=tuple(spec.columns),
            runner=self.runner,
        )
