import pytest
from pydantic import ValidationError

from omnis.adapters import RawLoadTaskType
from omnis.domain import RawLoad
from omnis.tests.fakes import FakeRunner


def test_builds_the_raw_load_with_its_runner():
    """
    Checks: a `raw_load` declaration becomes a RawLoad with its source, destination, columns and
    the runner the flow injected.

    If it fails: raw loads would read from another prefix, land into another table, declare other
    columns or run on the wrong runner than the ones written in tasks/*.yaml.
    """
    runner = FakeRunner()
    declaration = {"type": "raw_load", "source": "raw/new/t/", "destination": "raw.t", "columns": ["a", "b"]}

    raw_load = RawLoadTaskType(runner).build("raw.t", declaration)

    assert raw_load == RawLoad("raw.t", source="raw/new/t/", destination="raw.t", columns=("a", "b"), runner=runner)
    assert raw_load.runner is runner


@pytest.mark.parametrize("declaration", [
    {"type": "raw_load", "source": "raw/new/t/", "destination": "raw.t"},
    {"type": "raw_load", "source": "raw/new/t/", "destination": "raw.t", "columns": ["a"], "strategy": "merge"},
])
def test_an_invalid_declaration_fails(declaration):
    """
    Checks: a raw load declaration without `columns`, or with a key it doesn't take, is rejected.

    If it fails: mistakes in a raw load's YAML would be silently ignored when the DAG file is parsed.
    """
    with pytest.raises(ValidationError):
        RawLoadTaskType(FakeRunner()).build("raw.t", declaration)
