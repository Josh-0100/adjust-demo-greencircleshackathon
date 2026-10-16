#!/usr/bin/env bash
# Run Bolton Connect standalone. Reuses the repo backend venv if it exists,
# otherwise creates a module-local .venv and installs this module's deps.
set -euo pipefail

MODULE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$MODULE_ROOT/backend"
REPO_VENV="$MODULE_ROOT/../../backend/.venv"

if [[ -x "$REPO_VENV/bin/python" ]]; then
  PY="$REPO_VENV/bin/python"
else
  if [[ ! -x "$MODULE_ROOT/.venv/bin/python" ]]; then
    python3 -m venv "$MODULE_ROOT/.venv"
    "$MODULE_ROOT/.venv/bin/python" -m pip install --quiet --upgrade pip
    "$MODULE_ROOT/.venv/bin/python" -m pip install --quiet -r "$MODULE_ROOT/requirements.txt"
  fi
  PY="$MODULE_ROOT/.venv/bin/python"
fi

HOST="${BOLTON_HOST:-127.0.0.1}"
PORT="${BOLTON_PORT:-8099}"

echo "Bolton Connect → http://$HOST:$PORT  (resident portal at /, adviser view at /adviser.html)"
cd "$BACKEND_DIR"
exec "$PY" -m uvicorn bolton_api.app:app --host "$HOST" --port "$PORT" "$@"
