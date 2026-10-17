import yaml

from omnis.domain import Etl, WriteStrategy
from omnis.ports import EtlParser
from omnis.schemas import EtlFile


def load_yaml_mapping(name: str, content: bytes) -> dict:
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError(f"'{name}': expected a YAML mapping")
    return data


class YamlEtlParser(EtlParser):
    """ETLs written as YAML files (see schemas.EtlFile)."""

    extension = "yaml"

    def parse(self, name: str, content: bytes) -> Etl:
        spec = EtlFile(**load_yaml_mapping(name, content))
        return Etl(
            name=name,
            destination=spec.destination,
            pipe=spec.pipe,
            strategy=WriteStrategy(spec.strategy),
            key=tuple(spec.key),
            pre_statement=spec.pre_statement,
            post_statement=spec.post_statement,
        )
