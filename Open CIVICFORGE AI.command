#!/bin/bash
# Double-click in Finder to start the local demo and open it in the browser.
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)" || exit 1
cd "$PROJECT_DIR" || exit 1

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This launcher is for macOS. Use the Windows .bat file on Windows."
  exit 1
fi

# Finder may use a shorter PATH than an interactive Terminal session.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if { ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1 || ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)' >/dev/null 2>&1; } && [[ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]]; then
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
  # nvm is an external shell script and may reference unset shell variables.
  set +u
  . "$NVM_DIR/nvm.sh"
  set -u
fi

echo "Starting Adjust AI from $PROJECT_DIR"
echo "Keep this Terminal window open while using the app. Press Control-C to stop it."
"$PROJECT_DIR/scripts/start.sh" --open
status=$?

if [[ "$status" -ne 0 && "$status" -ne 130 ]]; then
  echo
  echo "Adjust AI could not start. Read the error above for the next step."
  read -r -p "Press Return to close this window..." _
fi
exit "$status"
