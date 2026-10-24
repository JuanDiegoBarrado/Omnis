from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from omnis.domain.table import Table
from omnis.domain.tasks.task import Task

if TYPE_CHECKING:
    from omnis.ports import TaskRunner


@dataclass(frozen=True)
class DDL(Task):
    """
    Applies the DDL of every table of a flow. It is the first task of every run, so it is not
    declared: no task of the flow can take its name.
    """

    NAME: ClassVar[str] = "create_tables"

    tables: tuple[Table, ...]
    name: str = NAME
    runner: TaskRunner[DDL] = field(kw_only=True, compare=False, repr=False)

    @property
    def doc(self) -> str:
        return "Apply the DDL of every table of the flow. Tables that already exist are left as they are."
