#!/bin/bash
# ghost-publisher launcher.
#
# Uses the project virtualenv at .venv if it exists, otherwise the system
# python3. This is the script launchd/cron calls, so it must not assume any
# particular shell environment — everything is resolved from its own location.
#
# Usage:
#   ./run.sh run --dry-run
#   ./run.sh run
#   ./run.sh status

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
    PYTHON="$PROJECT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
else
    echo "ghost-publisher: no python3 found on PATH" >&2
    exit 2
fi

exec "$PYTHON" -m ghost_publisher "$@"
