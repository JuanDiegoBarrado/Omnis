import yaml

from omnis.ports import Parser


class YamlParser(Parser[dict]):
    """
    Files written as a YAML mapping, read as they are: what the keys mean is up to whoever
    reads the mapping.
    """

    format = "yaml"

    def parse(self, name: str, content: bytes) -> dict:
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            raise ValueError(f"'{name}': expected a YAML mapping")
        return data
