from collections import Counter
from collections.abc import Iterable, Mapping

from omnis.domain.etl import Etl
from omnis.domain.raw_load import RawLoad

Node = Etl | RawLoad


class EtlGraph:
    """
    A data flow: its nodes and the dependencies between them.

    On creation it checks that every dependency points to a node of the graph, that there are
    no cycles and that each destination table has a single producer.
    """

    def __init__(self, name: str, nodes: Iterable[Node], dependencies: Mapping[str, Iterable[str]]):
        self.name = name

        self._nodes: dict[str, Node] = {}
        for node in nodes:
            if node.name in self._nodes:
                raise ValueError(f"Flow '{name}': node '{node.name}' is defined twice")
            self._nodes[node.name] = node

        unknown = sorted(set(dependencies) - set(self._nodes))
        if unknown:
            raise ValueError(f"Flow '{name}': dependencies declared for unknown nodes {unknown}")
        self._upstream = {node_name: tuple(dependencies.get(node_name, ())) for node_name in self._nodes}
        for node_name, upstream in self._upstream.items():
            missing = [up for up in upstream if up not in self._nodes]
            if missing:
                raise ValueError(f"Flow '{name}': node '{node_name}' depends on unknown nodes {missing}")

        producers = Counter(node.destination for node in self._nodes.values())
        shared = sorted(table for table, count in producers.items() if count > 1)
        if shared:
            raise ValueError(f"Flow '{name}': tables written by more than one node {shared}")

        self._order = self._topological_order()

    @property
    def nodes(self) -> list[Node]:
        """Every node, each one after all of its dependencies."""
        return [self._nodes[node_name] for node_name in self._order]

    def node(self, name: str) -> Node:
        return self._nodes[name]

    def upstream(self, name: str) -> tuple[str, ...]:
        """The nodes that must finish before `name` runs."""
        return self._upstream[name]

    def roots(self) -> list[str]:
        """The nodes that depend on nothing."""
        return [node_name for node_name in self._order if not self._upstream[node_name]]

    def _topological_order(self) -> list[str]:
        pending = {node_name: set(upstream) for node_name, upstream in self._upstream.items()}
        order = []
        while pending:
            ready = sorted(node_name for node_name, upstream in pending.items() if not upstream)
            if not ready:
                raise ValueError(f"Flow '{self.name}': dependency cycle among {sorted(pending)}")
            for node_name in ready:
                order.append(node_name)
                del pending[node_name]
            for upstream in pending.values():
                upstream.difference_update(ready)
        return order
