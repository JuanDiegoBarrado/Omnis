"""Checks the real flows in dags/: their artifacts must load into a valid Flow."""
import pytest

from omnis.container import ARTIFACTS_DIR, GRAPH_FILE_NAME, load_flow

# A flow is a folder of dags/ with a graph; folders being started (no graph yet) are skipped
FLOWS = sorted(path.parent.name for path in ARTIFACTS_DIR.glob(f"*/{GRAPH_FILE_NAME}.yaml"))


def test_there_is_at_least_one_flow():
    assert FLOWS


@pytest.mark.parametrize("flow", FLOWS)
def test_every_flow_has_its_dag_file(flow):
    assert (ARTIFACTS_DIR / flow / f"{flow}.py").is_file()


@pytest.mark.parametrize("flow", FLOWS)
def test_every_flow_loads(flow):
    # Flow checks pipes, destination DDL and raw landing tables
    assert load_flow(flow).nodes
