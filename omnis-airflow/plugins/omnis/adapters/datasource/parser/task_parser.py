from omnis.domain import Task
from omnis.ports import Parser, TaskType


class TaskParser(Parser[Task]):
    """
    Tasks declared one per mapping, in the format `declaration_parser` reads. The `type` of each
    declaration says which of `task_types` builds it; the flow only supports those.
    """

    def __init__(self, declaration_parser: Parser[dict], task_types: list[TaskType]):
        self.declaration_parser = declaration_parser
        self.format = declaration_parser.format
        self._task_types: dict[str, TaskType] = {}
        for task_type in task_types:
            if task_type.name in self._task_types:
                raise ValueError(f"Two task types are named '{task_type.name}'")
            self._task_types[task_type.name] = task_type

    def parse(self, name: str, content: bytes) -> Task:
        declaration = self.declaration_parser.parse(name, content)
        type_name = declaration.get("type")
        task_type = self._task_types.get(type_name) if isinstance(type_name, str) else None
        if task_type is None:
            problem = "no type" if type_name is None else f"unknown type {type_name!r}"
            raise ValueError(f"{problem}, expected one of {sorted(self._task_types)}")
        return task_type.build(name, declaration)
