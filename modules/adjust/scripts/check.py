#!/usr/bin/env python3
"""Run ADJUST checks without rebuilding or testing the host application."""
import argparse
import os
import subprocess
import sys
import time

from start import BACKEND, FRONTEND, ROOT, identity, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--e2e", action="store_true", help="Also start isolated test servers and exercise the browser workflow.")
    args = parser.parse_args()
    python, node = prepare()
    env = {**os.environ, "NEXT_TELEMETRY_DISABLED": "1", "ADJUST_BUILD_DIR": ".next-check"}
    commands = [
        ([python, "-m", "pytest"], BACKEND),
        ([node, str(FRONTEND / "node_modules/typescript/bin/tsc"), "--noEmit"], FRONTEND),
        ([node, str(FRONTEND / "node_modules/vitest/vitest.mjs"), "run"], FRONTEND),
        ([node, str(FRONTEND / "node_modules/next/dist/bin/next"), "build"], FRONTEND),
    ]
    for command, cwd in commands:
        print(f"\nChecking ADJUST: {' '.join(str(arg) for arg in command)}", flush=True)
        subprocess.run(command, cwd=cwd, env=env, check=True)
    if args.e2e:
        url = os.environ.get("ADJUST_TEST_URL", "http://127.0.0.1:3186")
        process = None
        try:
            if not os.environ.get("ADJUST_TEST_URL"):
                server_env = {**env, "ADJUST_API_PORT": "8786", "ADJUST_UI_PORT": "3186", "ADJUST_BUILD_DIR": ".next-e2e"}
                process = subprocess.Popen([sys.executable, str(ROOT / "scripts/start.py"), "--no-open"], env=server_env)
                for _ in range(90):
                    if process.poll() is not None:
                        raise RuntimeError("ADJUST test servers failed to start")
                    if identity(url):
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError("ADJUST test servers did not become ready")
            subprocess.run([node, str(FRONTEND / "node_modules/@playwright/test/cli.js"), "test"], cwd=FRONTEND,
                           env={**env, "ADJUST_TEST_URL": url}, check=True)
        finally:
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
    print("\nAll requested ADJUST checks passed.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"ADJUST checks failed: {error}", file=sys.stderr)
        sys.exit(1)
