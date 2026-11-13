#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "Error: Python 3 is required but was not found on PATH." >&2
    exit 2
fi

"$PYTHON_CMD" -c "import rich, psutil, matplotlib" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Error: Missing required Python packages (rich, psutil, matplotlib)." >&2
    echo "Install them with: $PYTHON_CMD -m pip install -r requirements.txt" >&2
    exit 3
fi

mkdir -p data/demo data/jobs data/configuration reports logs

"$PYTHON_CMD" main.py
EXIT_CODE=$?
exit "$EXIT_CODE"

