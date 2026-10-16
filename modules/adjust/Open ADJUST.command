#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  exec python3 scripts/start.py
fi
echo "Install Python 3.11–3.13 and Node.js 22+, then open this launcher again."
read -r -p "Press Enter to close."
