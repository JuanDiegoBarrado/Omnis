from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from omnis.domain import Etl, WriteStrategy
from omnis.ports import PipeRepository, TaskRunner, TaskType


class EtlDeclaration(BaseModel):
    """What the declaration of an ETL task says (`type: etl`)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["etl"]
    destination: str
    pipe: str
    strategy: Literal["full_rebuild", "merge"] = "full_rebuild"
    key: list[str] = Field(default_factory=list)
    pre_statement: str | None = None
    post_statement: str | None = None


class EtlTaskType(TaskType):
    """ETL tasks (see EtlDeclaration): the pipe they name is looked up in the pipe repository."""

    name = "etl"

    def __init__(self, pipe_repository: PipeRepository, runner: TaskRunner[Etl]):
        self.pipe_repository = pipe_repository
        self.runner = runner

    def build(self, name: str, declaration: dict) -> Etl:
        spec = EtlDeclaration.model_validate(declaration)
        pipe = self.pipe_repository.find(spec.pipe)
        if pipe is None:
            raise ValueError(f"ETL '{name}': pipe '{spec.pipe}' not found")
        return Etl(
            name=name,
            destination=spec.destination,
            pipe=pipe,
            strategy=WriteStrategy(spec.strategy),
            key=tuple(spec.key),
            pre_statement=spec.pre_statement,
            post_statement=spec.post_statement,
            runner=self.runner,
        )
