#!/bin/bash
# Bolton Connect — double-click launcher (macOS).
# Starts the EXISTING standalone app and opens the EXISTING resident interface.
# It does NOT modify any UI/UX; it only runs the server that already ships in
# this module (scripts/run.sh) and opens the browser to the existing portal.
set -euo pipefail
cd "$(dirname "$0")"

HOST="127.0.0.1"
PORT="8099"
URL="http://$HOST:$PORT/"
HEALTH="http://$HOST:$PORT/api/bolton-connect/health"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Install Python 3.11-3.13, then open this launcher again."
  read -r -p "Press Enter to close."
  exit 1
fi

# If it is already running, just open the existing UI and stop.
if curl -s -o /dev/null "$HEALTH" 2>/dev/null; then
  echo "Bolton Connect is already running - opening $URL"
  open "$URL"
  exit 0
fi

echo "Starting Bolton Connect ..."
# Open the existing resident portal once the server answers, then keep the
# server in the foreground (close this Terminal window to stop it).
( for _ in $(seq 1 40); do
    if curl -s -o /dev/null "$HEALTH" 2>/dev/null; then
      open "$URL"
      break
    fi
    sleep 1
  done ) &

exec ./scripts/run.sh
