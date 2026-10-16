#!/usr/bin/env python3
"""Prepare and launch the local app; invoked by the Windows double-click file."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
ADJUST_FRONTEND = ROOT / "modules" / "adjust" / "frontend"
VENV = BACKEND / ".venv"
PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
CHILDREN = []


def probe(command, *, cwd=ROOT, shell=False):
    try:
        return subprocess.run(command, cwd=cwd, shell=shell, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, check=False).returncode == 0
    except OSError:
        return False


def spawn(command, *, cwd, env=None, shell=False):
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    child = subprocess.Popen(command, cwd=cwd, env=env, shell=shell, **options)
    CHILDREN.append(child)
    return child


def run(command, *, cwd=ROOT, env=None, shell=False):
    if spawn(command, cwd=cwd, env=env, shell=shell).wait() != 0:
        raise RuntimeError("Setup failed. Read the dependency error above, then try again.")


def cleanup():
    for child in reversed(CHILDREN):
        if child.poll() is not None:
            continue
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    for child in CHILDREN:
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name != "nt":
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            child.wait(timeout=5)


def prepare():
    supported = "import sys; sys.exit(0 if (3, 11) <= sys.version_info[:2] < (3, 14) else 1)"
    if not probe([str(PYTHON), "-c", supported]):
        print("Preparing Python environment (Python 3.11-3.13 required)...", flush=True)
        run([sys.executable, "-m", "venv", "--clear", str(VENV)])
    packages = r"""
import importlib, importlib.metadata as metadata, pathlib, re
for line in pathlib.Path('backend/requirements.txt').read_text().splitlines():
    match = re.match(r'([A-Za-z0-9_-]+)(?:\[[^\]]+\])?==([^ ;]+)', line)
    if match:
        assert metadata.version(match[1]) == match[2]
for name in ('fastapi', 'uvicorn', 'sqlalchemy', 'alembic', 'pydantic',
             'pydantic_settings', 'yaml', 'httpx', 'psycopg', 'pytest', 'dotenv'):
    importlib.import_module(name)
"""
    has_pip = probe([str(PYTHON), "-m", "pip", "--version"])
    if not probe([str(PYTHON), "-c", packages]) or (has_pip and not probe([str(PYTHON), "-m", "pip", "check"])):
        print("Installing backend dependencies; first setup needs internet access...", flush=True)
        if not has_pip:
            run([str(PYTHON), "-m", "ensurepip", "--upgrade"])
        run([str(PYTHON), "-m", "pip", "install", "-r", str(BACKEND / "requirements.txt")])
        if not probe([str(PYTHON), "-c", packages]) or not probe([str(PYTHON), "-m", "pip", "check"]):
            raise RuntimeError("Backend dependencies remain incomplete. See the installation output above.")
    # Read dotenv as data through the installed library. Never execute .env as shell code.
    result = subprocess.run([str(PYTHON), "-c",
                             "import json; from dotenv import dotenv_values; print(json.dumps(dotenv_values('.env')))"],
                            cwd=ROOT, capture_output=True, text=True, check=True)
    env = os.environ.copy()
    for name, value in json.loads(result.stdout).items():
        if value is not None:
            env.setdefault(name, value)
    return env


def port_value(env, name, default):
    value = env.get(name) or str(default)
    if not re.fullmatch(r"[0-9]+", value) or not 1 <= int(value) <= 65535:
        raise RuntimeError(f"{name} must be a port between 1 and 65535.")
    return int(value)


def healthy(base, expected_demo=None):
    try:
        def get(path):
            with urllib.request.urlopen(base + path, timeout=2) as response:
                return json.load(response)
        health = get("/api/health")
        modules = get("/api/modules").get("modules")
        bolton = get("/api/bolton-connect/health")
        adjust = get("/api/adjust/health")
        return (health.get("status") == "ok" and isinstance(health.get("demo_mode"), bool)
                and (expected_demo is None or health["demo_mode"] == expected_demo)
                and bolton.get("demo_mode") == health["demo_mode"]
                and bolton.get("status") == "ok" and adjust.get("status") == "ok"
                and isinstance(health.get("provider"), str) and isinstance(modules, list)
                and bool(modules) and all(isinstance(item, dict) and "id" in item
                                         and "name" in item and "enabled" in item for item in modules))
    except (OSError, urllib.error.URLError, ValueError, AttributeError):
        return False


def ensure_free(port):
    with socket.socket() as listener:
        try:
            if os.name != "nt":
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("127.0.0.1", port))
        except OSError as error:
            raise RuntimeError(f"Port {port} is occupied by an unavailable or different application. "
                               "Stop that process or change the port in .env.") from error


def wait_ready(base, children, seconds, expected_demo=None):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if any(child.poll() is not None for child in children):
            raise RuntimeError("A server stopped. Check its diagnostic output above.")
        if healthy(base, expected_demo):
            return
        time.sleep(0.5)
    raise RuntimeError(f"The application did not become ready at {base}. Check the server output above.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-open", action="store_true", help="Start without opening the browser")
    args = parser.parse_args()
    if not (3, 11) <= sys.version_info[:2] < (3, 14):
        raise RuntimeError("Install Python 3.11-3.13, or set CIVICFORGE_PYTHON to its executable.")
    node, npm = shutil.which("node"), shutil.which("npm")
    if not node or not npm or not probe([node, "-e", "process.exit(Number(process.versions.node.split('.')[0]) >= 22 ? 0 : 1)"]):
        raise RuntimeError("Install Node.js 22+ with npm, reopen this launcher, and try again.")
    env = prepare()
    mode = env.get("DEMO_MODE", "true").lower()
    if mode not in {"true", "1", "yes", "y", "t", "on", "false", "0", "no", "n", "f", "off"}:
        raise RuntimeError("DEMO_MODE must be true or false.")
    expected_demo = mode in {"true", "1", "yes", "y", "t", "on"}
    backend_port = port_value(env, "BACKEND_PORT", 8765)
    frontend_port = port_value(env, "FRONTEND_PORT", 3000)
    adjust_port = port_value(env, "ADJUST_EMBED_PORT", 3002)
    if len({backend_port, frontend_port, adjust_port}) != 3:
        raise RuntimeError("BACKEND_PORT, FRONTEND_PORT and ADJUST_EMBED_PORT must be different.")
    api = f"http://127.0.0.1:{backend_port}"
    site = f"http://127.0.0.1:{frontend_port}"
    env["BACKEND_URL"] = env.get("BACKEND_URL") or api
    env["ADJUST_FRONTEND_URL"] = f"http://127.0.0.1:{adjust_port}"
    adjust_env = {**env, "ADJUST_BASE_PATH": "/modules/adjust", "ADJUST_EMBEDDED": "1",
                  "ADJUST_BACKEND_URL": api, "ADJUST_BUILD_DIR": ".next-civicforge"}
    existing_api, existing_site = healthy(api, expected_demo), healthy(site, expected_demo)
    if not existing_api and healthy(api):
        raise RuntimeError("The running application uses a different DEMO_MODE. Stop its launcher, then restart with the requested settings.")
    def adjust_ready():
        try:
            with urllib.request.urlopen(f"{env['ADJUST_FRONTEND_URL']}/modules/adjust", timeout=3) as response:
                return response.status == 200 and b"Adjust AI" in response.read()
        except (OSError, ValueError):
            return False
    existing_adjust = adjust_ready()
    if existing_api and existing_site and existing_adjust:
        print(f"Adjust AI is already running at {site}/", flush=True)
        if not args.no_open:
            webbrowser.open(f"{site}/")
        return
    for port, available in ((backend_port, existing_api), (frontend_port, existing_site), (adjust_port, existing_adjust)):
        if not available:
            ensure_free(port)
    packages = """
const fs = require('fs'), path = require('path'), pkg = require('./package.json');
for (const name of Object.keys({...pkg.dependencies, ...pkg.devDependencies})) {
    if (!fs.existsSync(path.join('node_modules', name, 'package.json'))) process.exit(1);
}
if (['win32', 'darwin'].includes(process.platform)) {
    const name = '@next/swc-' + process.platform + '-' + process.arch + (process.platform === 'win32' ? '-msvc' : '');
    require(name);
}
if (!fs.existsSync('node_modules/next/dist/bin/next')) process.exit(1);
"""
    for workspace in (FRONTEND, ADJUST_FRONTEND):
        if not probe([node, "-e", packages], cwd=workspace) or not probe([npm, "ls", "--depth=0"], cwd=workspace, shell=os.name == "nt"):
            print(f"Installing {workspace.name} dependencies; first setup needs internet access...", flush=True)
            run([npm, "ci"], cwd=workspace, env=env, shell=os.name == "nt")
            if not probe([node, "-e", packages], cwd=workspace):
                raise RuntimeError("Frontend dependencies remain incomplete. See the installation output above.")
    servers = []
    if not existing_api:
        servers.append(spawn([str(PYTHON), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                              "--port", str(backend_port)], cwd=BACKEND, env=env))
    wait_ready(api, servers, 30, expected_demo)
    if not existing_adjust:
        servers.append(spawn([node, str(ADJUST_FRONTEND / "node_modules/next/dist/bin/next"), "dev",
                              "--hostname", "127.0.0.1", "--port", str(adjust_port)], cwd=ADJUST_FRONTEND, env=adjust_env))
    if not existing_site:
        servers.append(spawn([node, str(FRONTEND / "node_modules/next/dist/bin/next"), "dev",
                              "--hostname", "127.0.0.1", "--port", str(frontend_port)], cwd=FRONTEND, env=env))
    wait_ready(site, servers, 90, expected_demo)
    deadline = time.monotonic() + 90
    while not adjust_ready():
        if time.monotonic() >= deadline or any(child.poll() is not None for child in servers):
            raise RuntimeError("The integrated Adjust AI interface did not become ready. See its server output above.")
        time.sleep(0.5)
    try:
        with urllib.request.urlopen(f"{site}/", timeout=45) as response:
            if response.status != 200 or b"<html" not in response.read(4096).lower():
                raise ValueError("Unexpected landing page response")
    except (OSError, urllib.error.URLError, ValueError) as error:
        raise RuntimeError(f"The landing page did not load at {site}/. Check the frontend output above.") from error
    print(f"Adjust AI: {site}/\nKeep this window open. Press Ctrl+C to stop the servers started here.", flush=True)
    if not args.no_open:
        webbrowser.open(f"{site}/")
    while all(child.poll() is None for child in servers):
        time.sleep(1)
    raise RuntimeError("A server stopped. Check its diagnostic output above.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping Adjust AI...", flush=True)
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"\nERROR: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
    finally:
        cleanup()
