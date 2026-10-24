from collections.abc import Iterable, Mapping


class TaskDependencies:
    """
    Which task of a flow precedes which: the names of its tasks and the dependencies between
    them, nothing else.

    On creation it checks that every dependency points to a node of the graph and that there
    are no cycles.
    """

    def __init__(self, dependencies: Mapping[str, Iterable[str]]):
        self._upstream = {name: tuple(upstream) for name, upstream in dependencies.items()}
        for name, upstream in self._upstream.items():
            missing = [up for up in upstream if up not in self._upstream]
            if missing:
                raise ValueError(f"Graph: node '{name}' depends on unknown nodes {missing}")

        self._order = self._topological_order()

    @property
    def tasks(self) -> list[str]:
        """Every node, each one after all of its dependencies."""
        return list(self._order)

    def preceding_tasks(self, name: str) -> tuple[str, ...]:
        """The nodes that must finish before `name` runs."""
        return self._upstream[name]

    def roots(self) -> list[str]:
        """The nodes that depend on nothing."""
        return [name for name in self._order if not self._upstream[name]]

    def _topological_order(self) -> list[str]:
        pending = {name: set(upstream) for name, upstream in self._upstream.items()}
        order = []
        while pending:
            ready = sorted(name for name, upstream in pending.items() if not upstream)
            if not ready:
                raise ValueError(f"Graph: dependency cycle among {sorted(pending)}")
            for name in ready:
                order.append(name)
                del pending[name]
            for upstream in pending.values():
                upstream.difference_update(ready)
        return order
