from collections.abc import Iterable

from omnis.domain.etl import Etl
from omnis.domain.etl_graph import EtlGraph, Node
from omnis.domain.pipe import Pipe
from omnis.domain.raw_load import RawLoad
from omnis.domain.table import Table


class Flow:
    """
    A flow ready to run: its graph, the pipe of every ETL and the tables it needs.

    On creation it checks that every ETL has its pipe and the DDL of its destination, and that
    no raw landing table has DDL (a raw load drops and recreates its destination on every run).
    Tables are named after the table they create.
    """

    def __init__(self, graph: EtlGraph, pipes: Iterable[Pipe], tables: Iterable[Table]):
        self.graph = graph
        self.tables = list(tables)

        available = {pipe.name: pipe for pipe in pipes}
        etls = [node for node in graph.nodes if isinstance(node, Etl)]
        missing = sorted({etl.pipe for etl in etls} - set(available))
        if missing:
            raise ValueError(f"Flow '{self.name}': pipes {missing} not found")
        self._pipes = {etl.name: available[etl.pipe] for etl in etls}

        declared = {table.name for table in self.tables}
        undeclared = sorted(etl.destination for etl in etls if etl.destination not in declared)
        if undeclared:
            raise ValueError(f"Flow '{self.name}': ETL destinations without DDL {undeclared}")
        clashing = sorted(
            node.destination for node in graph.nodes if isinstance(node, RawLoad) and node.destination in declared
        )
        if clashing:
            raise ValueError(f"Flow '{self.name}': raw landing tables must not have DDL {clashing}")

    @property
    def name(self) -> str:
        return self.graph.name

    @property
    def nodes(self) -> list[Node]:
        """Every node, each one after all of its dependencies."""
        return self.graph.nodes

    def upstream(self, name: str) -> tuple[str, ...]:
        """The nodes that must finish before `name` runs."""
        return self.graph.upstream(name)

    def pipe_of(self, etl: Etl) -> Pipe:
        return self._pipes[etl.name]
