import sys
from pathlib import Path

# Airflow puts plugins/ on sys.path; mirror it so tests import `omnis` the same way
PLUGINS_DIR = Path(__file__).resolve().parents[1] / "plugins"
if str(PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGINS_DIR))
