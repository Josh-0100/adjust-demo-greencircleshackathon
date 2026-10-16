#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
command -v npm >/dev/null || { echo 'Install Node.js 22+ and npm first.'; exit 1; }
if [[ ! -x backend/.venv/bin/python ]]; then
  PYTHON_BIN="${CIVICFORGE_PYTHON:-}"
  if [[ -z "$PYTHON_BIN" ]]; then
    for candidate in python3.13 python3.12 python3.11 python3; do
      if command -v "$candidate" >/dev/null && "$candidate" -c 'import sys; assert (3, 11) <= sys.version_info[:2] < (3, 14)' 2>/dev/null; then
        PYTHON_BIN="$candidate"
        break
      fi
    done
  fi
  [[ -n "$PYTHON_BIN" ]] || { echo 'Install Python 3.11–3.13 or set CIVICFORGE_PYTHON to its executable.'; exit 1; }
  "$PYTHON_BIN" -m venv backend/.venv
fi
if command -v uv >/dev/null; then
  UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/civicforge-uv-cache}" uv pip install --python backend/.venv/bin/python -r backend/requirements.txt
else
  backend/.venv/bin/python -m pip install -r backend/requirements.txt
fi
(
  cd frontend
  npm ci --cache "${npm_config_cache:-/tmp/civicforge-npm-cache}"
)
(
  cd modules/adjust/frontend
  npm ci --cache "${npm_config_cache:-/tmp/civicforge-npm-cache}"
)
(
  cd backend
  .venv/bin/python -m app.database.bootstrap
)
echo 'Dependencies installed and database initialised. Run ./scripts/start.sh to start the integrated application.'
