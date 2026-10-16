#!/usr/bin/env python3
"""Start ADJUST only. Reuse installed runtimes without altering the host app."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"


def run(args, **kwargs):
    subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def python_runtime():
    candidates = [os.environ.get("ADJUST_PYTHON", ""),
                  str(ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")),
                  str(REPO / "backend" / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")),
                  shutil.which("python3.13"), shutil.which("python3.12"), shutil.which("python3.11"), sys.executable]
    for candidate in filter(None, candidates):
        try:
            version = subprocess.check_output([candidate, "-c", "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))"], text=True).strip()
            if version in {"3.11", "3.12", "3.13"}:
                return candidate
        except (OSError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("Install Python 3.11–3.13, or set ADJUST_PYTHON to its executable.")


def prepare():
    node, npm = shutil.which("node"), shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not node or not npm or int(subprocess.check_output([node, "--version"], text=True).strip().lstrip("v").split(".")[0]) < 22:
        raise RuntimeError("Install Node.js 22 or newer, including npm.")
    python = python_runtime()
    imports = subprocess.run([python, "-c", "import fastapi, uvicorn, pydantic, httpx, pytest"], capture_output=True)
    if imports.returncode:
        local_python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not local_python.exists():
            run([python, "-m", "venv", ROOT / ".venv"])
        python = str(local_python)
        run([python, "-m", "ensurepip", "--upgrade"])
        run([python, "-m", "pip", "install", "-r", BACKEND / "requirements.txt"])
    modules = FRONTEND / "node_modules"
    shared = REPO / "frontend" / "node_modules"
    if not modules.exists() and (shared / "next" / "dist" / "bin" / "next").exists() and os.name != "nt":
        modules.symlink_to(os.path.relpath(shared, FRONTEND), target_is_directory=True)
    if not (modules / "next" / "dist" / "bin" / "next").exists():
        run([npm, "install", "--no-audit", "--no-fund"], cwd=FRONTEND)
    return python, node


def identity(url):
    try:
        with urllib.request.urlopen(url + "/api/adjust/health", timeout=2) as response:
            data = json.load(response)
        return data.get("module") == "adjust" and data.get("data_persisted") is False
    except Exception:
        return False


def check_port(port):
    with socket.socket() as connection:
        if os.name != "nt":
            # Recently closed sockets can remain in TIME_WAIT after a restart.
            # This still rejects an active listener; avoid Windows' different
            # SO_REUSEADDR semantics, which can permit listener collisions.
            connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            connection.bind(("127.0.0.1", port))
        except PermissionError as error:
            raise RuntimeError("Local network access is restricted. Run the ADJUST launcher from your terminal.") from error
        except OSError as error:
            raise RuntimeError(f"Port {port} is occupied. Set ADJUST_API_PORT and ADJUST_UI_PORT to unused ports.") from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--setup-only", action="store_true")
    args = parser.parse_args()
    python, node = prepare()
    if args.setup_only:
        print(f"ADJUST dependencies ready. Python: {python}")
        return
    api_port = int(os.environ.get("ADJUST_API_PORT", "8766"))
    ui_port = int(os.environ.get("ADJUST_UI_PORT", "3001"))
    if api_port == ui_port or not all(1024 <= port <= 65535 for port in [api_port, ui_port]):
        raise RuntimeError("Choose distinct API/UI ports between 1024 and 65535.")
    backend_url, frontend_url = f"http://127.0.0.1:{api_port}", f"http://127.0.0.1:{ui_port}"
    if identity(backend_url) and identity(frontend_url):
        print(f"ADJUST is already running: {frontend_url}", flush=True)
        if not args.no_open:
            webbrowser.open(frontend_url)
        return
    check_port(api_port)
    check_port(ui_port)
    env = {**os.environ, "ADJUST_BACKEND_URL": backend_url, "NEXT_TELEMETRY_DISABLED": "1"}
    processes = []
    def stop(signum=None, frame=None):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    try:
        # No access logs; descriptions are never written to files or a database.
        processes.append(subprocess.Popen([python, "-m", "uvicorn", "adjust_api.main:app", "--host", "127.0.0.1", "--port", str(api_port), "--no-access-log", "--log-level", "critical"], cwd=BACKEND, env=env, start_new_session=os.name != "nt"))
        processes.append(subprocess.Popen([node, str(FRONTEND / "node_modules/next/dist/bin/next"), "dev", "--hostname", "127.0.0.1", "--port", str(ui_port)], cwd=FRONTEND, env=env, start_new_session=os.name != "nt"))
        for _ in range(90):
            if any(process.poll() is not None for process in processes):
                raise RuntimeError("An ADJUST server stopped during startup. Check its output above.")
            if identity(backend_url) and identity(frontend_url):
                # Confirm the two-sided page is ready as well as the proxy.
                with urllib.request.urlopen(frontend_url, timeout=20) as response:
                    if response.status != 200:
                        raise RuntimeError("The ADJUST page is not ready.")
                print(f"\nADJUST is ready: {frontend_url}\nIndependent API: {backend_url}/docs\nKeep this terminal open. Ctrl+C stops ADJUST.\n", flush=True)
                if not args.no_open:
                    webbrowser.open(frontend_url)
                break
            time.sleep(1)
        else:
            raise RuntimeError("ADJUST did not become ready within 90 seconds.")
        while all(process.poll() is None for process in processes):
            time.sleep(1)
        raise RuntimeError("An ADJUST server stopped. Restart the launcher to try again.")
    except KeyboardInterrupt:
        print("\nStopping ADJUST…", flush=True)
    finally:
        for process in reversed(processes):
            if process.poll() is not None:
                continue
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
            else:
                os.killpg(process.pid, signal.SIGTERM)
        for process in processes:
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                if os.name != "nt":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"ADJUST: {error}", file=sys.stderr)
        sys.exit(1)
