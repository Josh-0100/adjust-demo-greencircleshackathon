#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"
.venv/bin/python -m pytest -q
cd "$ROOT/modules/bolton-connect"
"$ROOT/backend/.venv/bin/python" -m pytest -q
cd "$ROOT/modules/adjust/backend"
"$ROOT/backend/.venv/bin/python" -m pytest -q
cd "$ROOT/modules/adjust/frontend"
npm run typecheck
npm run test
ADJUST_BASE_PATH=/modules/adjust ADJUST_EMBEDDED=1 ADJUST_BUILD_DIR=.next-integrated npm run build
cd "$ROOT/frontend"
npm run typecheck
npm run test
NEXT_BUILD_DIR=.next-validation npm run build
if [[ "${1:-}" == '--e2e' ]]; then
  npm run test:e2e
fi
