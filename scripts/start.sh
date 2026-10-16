#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ "$#" -gt 1 || ( "$#" -eq 1 && "${1:-}" != "--open" ) ]]; then
  echo 'Usage: ./scripts/start.sh [--open]' >&2
  exit 2
fi
if [[ ! -x backend/.venv/bin/python ]]; then
  "$ROOT/scripts/setup.sh"
fi
if [[ "${1:-}" == '--open' ]]; then
  exec backend/.venv/bin/python scripts/start_windows.py
else
  exec backend/.venv/bin/python scripts/start_windows.py --no-open
fi
