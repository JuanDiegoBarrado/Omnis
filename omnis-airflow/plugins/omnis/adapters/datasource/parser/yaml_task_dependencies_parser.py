from pydantic import BaseModel, ConfigDict, Field

from omnis.adapters.datasource.parser.yaml_parser import YamlParser
from omnis.domain import TaskDependencies
from omnis.ports import Parser


class GraphNodeFile(BaseModel):
    """A node of the graph of a flow: only the tasks it runs after."""

    model_config = ConfigDict(extra="forbid")

    after: list[str] = Field(default_factory=list)


class TaskDependenciesFile(BaseModel):
    """Structure of the graph of a flow (graph.yaml)."""

    model_config = ConfigDict(extra="forbid")

    nodes: dict[str, GraphNodeFile]


class YamlTaskDependenciesParser(Parser[TaskDependencies]):
    """The graph of a flow written as a YAML file (see TaskDependenciesFile): which task precedes which."""

    format = "yaml"

    def parse(self, name: str, content: bytes) -> TaskDependencies:
        data = YamlParser().parse(name, content)
        # A node that runs after nothing can be written as a bare key
        data["nodes"] = {node: spec or {} for node, spec in (data.get("nodes") or {}).items()}
        spec = TaskDependenciesFile(**data)
        return TaskDependencies({node: node_spec.after for node, node_spec in spec.nodes.items()})
