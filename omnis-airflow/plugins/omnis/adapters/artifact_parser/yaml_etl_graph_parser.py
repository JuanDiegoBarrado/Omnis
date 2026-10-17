from omnis.adapters.artifact_parser.yaml_etl_parser import load_yaml_mapping
from omnis.domain import EtlGraph, RawLoad
from omnis.ports import EtlGraphParser, EtlRepository
from omnis.schemas import EtlGraphFile, RawLoadNodeFile


class YamlEtlGraphParser(EtlGraphParser):
    """
    The graph of the flow `flow` written as a YAML file (see schemas.EtlGraphFile). Its ETL
    nodes are resolved with the flow's EtlRepository.
    """

    extension = "yaml"

    def __init__(self, flow: str, etls: EtlRepository):
        self._flow = flow
        self._etls = etls

    def parse(self, name: str, content: bytes) -> EtlGraph:
        # Every flow names its graph file the same: the graph takes the flow's name, not the file's
        data = load_yaml_mapping(f"{self._flow}/{name}", content)
        # A node with nothing to declare can be written as a bare key
        data["nodes"] = {node: spec or {} for node, spec in (data.get("nodes") or {}).items()}
        spec = EtlGraphFile(**data)

        nodes = []
        for node_name, node_spec in spec.nodes.items():
            if isinstance(node_spec, RawLoadNodeFile):
                nodes.append(RawLoad(
                    name=node_name,
                    source=node_spec.source,
                    destination=node_spec.destination,
                    columns=tuple(node_spec.columns),
                ))
            else:
                etl = self._etls.find(node_name)
                if etl is None:
                    raise ValueError(f"Flow '{self._flow}': no ETL definition found for node '{node_name}'")
                nodes.append(etl)

        dependencies = {node_name: node_spec.after for node_name, node_spec in spec.nodes.items()}
        return EtlGraph(self._flow, nodes, dependencies)
