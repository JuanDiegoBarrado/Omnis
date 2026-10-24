import pytest

from omnis.adapters import TaskParser, YamlParser
from omnis.ports import TaskType
from omnis.tests.fakes import FakeTask


class NamedTaskType(TaskType):
    """Builds a FakeTask, remembering the declarations it was given."""

    def __init__(self, name: str):
        self.name = name
        self.declarations: list[dict] = []

    def build(self, name: str, declaration: dict) -> FakeTask:
        self.declarations.append(declaration)
        return FakeTask(name)


def test_each_declaration_is_built_by_the_task_type_of_its_type():
    """
    Checks: a declaration goes to the TaskType whose name is its `type`, with all its keys, and
    the other task types are not used.

    If it fails: tasks would be built by the wrong type (a raw load built as an ETL) or get their
    declaration incomplete. This is how the pluggable task types are dispatched.
    """
    etl, raw_load = NamedTaskType("etl"), NamedTaskType("raw_load")
    parser = TaskParser(YamlParser(), task_types=[etl, raw_load])

    task = parser.parse("orig.t", b"type: raw_load\nsource: raw/new/t/\n")

    assert task == FakeTask("orig.t")
    assert raw_load.declarations == [{"type": "raw_load", "source": "raw/new/t/"}]
    assert etl.declarations == []


def test_its_format_is_the_format_of_the_declarations():
    """
    Checks: the TaskParser reads files of the format of its declaration parser (yaml).

    If it fails: TaskRepository looks for tasks/*.<format>, so no task file would be found and
    every flow would report all its nodes as without definition.
    """
    assert TaskParser(YamlParser(), task_types=[]).format == "yaml"


@pytest.mark.parametrize(("content", "problem"), [
    (b"destination: orig.t\n", "no type"),
    (b"type: unknown\n", "unknown type 'unknown'"),
    (b"type: [etl]\n", "unknown type"),
])
def test_a_declaration_of_a_type_the_flow_does_not_support_fails(content, problem):
    """
    Checks: a declaration without `type`, with a type the flow did not register, or with a type
    that isn't a string is rejected, listing the types the flow supports.

    If it fails: a task with a misspelled or unregistered type would crash with an unclear error,
    or be built by no one, instead of a DAG import error saying which types are valid.
    """
    parser = TaskParser(YamlParser(), task_types=[NamedTaskType("etl")])

    with pytest.raises(ValueError, match=rf"{problem}.*expected one of \['etl'\]"):
        parser.parse("orig.t", content)


def test_two_task_types_cannot_share_a_name():
    """
    Checks: registering two task types with the same name in a flow is rejected.

    If it fails: one of them would silently replace the other, and every declaration of that type
    would be built by whichever was registered last (with its runner).
    """
    with pytest.raises(ValueError, match="Two task types are named 'etl'"):
        TaskParser(YamlParser(), task_types=[NamedTaskType("etl"), NamedTaskType("etl")])
