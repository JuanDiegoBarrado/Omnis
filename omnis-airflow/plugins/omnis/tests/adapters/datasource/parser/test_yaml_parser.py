import pytest

from omnis.adapters import YamlParser


def test_reads_a_mapping_as_it_is():
    """
    Checks: a YAML mapping is read into a dict with its keys and values unchanged.

    If it fails: every task declaration (tasks/*.yaml) would reach its TaskType changed or empty,
    so tasks would be built with the wrong settings.
    """
    assert YamlParser().parse("t", b"type: etl\nkey: [a, b]\n") == {"type": "etl", "key": ["a", "b"]}


@pytest.mark.parametrize("content", [b"", b"- a\n- b\n", b"just text"])
def test_anything_but_a_mapping_fails(content):
    """
    Checks: an empty file, a YAML list or plain text is rejected with a ValueError.

    If it fails: an empty or malformed task file would get past the parser and break later with an
    AttributeError that doesn't say which file is wrong, instead of an error naming the file.
    """
    with pytest.raises(ValueError, match="expected a YAML mapping"):
        YamlParser().parse("t", content)
