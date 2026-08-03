"""Make the project importable for tests.

Without this, `pytest tests/` fails to import `ghost_publisher` (only
`python -m pytest` puts the working directory on `sys.path`). The package is
not installed — it is run in place via `run.sh` — so the path is added here.
"""

import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
