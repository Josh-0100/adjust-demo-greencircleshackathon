"""Vercel entrypoint for the existing host and its two independent modules.

This public deployment is a fictional demonstration, not a durable case store.
Each function worker receives fresh, separate SQLite stores in its writable
temporary directory. The source databases and local .env files are never used.
The application's original lifespan still runs its migrations and module seeds.
"""
from pathlib import Path
import os
import shutil
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="adjust-public-demo-"))
CONFIG_PATH = RUNTIME_DIR / "challenge_config.yaml"
shutil.copyfile(ROOT / "config" / "challenge_config.yaml", CONFIG_PATH)

# Configure before importing the host: its module-level application also creates
# child applications. Override deployment/local settings deliberately so this
# public, synthetic demo cannot inherit real databases, credentials or providers.
os.environ.update({
    "DEMO_MODE": "true",
    "DATABASE_URL": f"sqlite:///{RUNTIME_DIR / 'host.db'}",
    "CHALLENGE_CONFIG_PATH": str(CONFIG_PATH),
    "CORS_ORIGINS": "",
    "STAFF_API_TOKEN": "",
    "ADMIN_API_TOKEN": "",
    "LLM_PROVIDER": "deterministic",
    "LLM_BASE_URL": "",
    "LLM_API_KEY": "",
    "LLM_MODEL": "",
    "BOLTON_DEMO_MODE": "true",
    "BOLTON_DATABASE_PATH": str(RUNTIME_DIR / "resident.db"),
    "BOLTON_DIRECTORY_PATH": str(ROOT / "modules" / "bolton-connect" / "data" / "support_directory.json"),
    "BOLTON_DEMO_RESIDENTS_PATH": str(ROOT / "modules" / "bolton-connect" / "data" / "demo_residents.json"),
    "BOLTON_FRONTEND_DIR": str(ROOT / "modules" / "bolton-connect" / "frontend"),
    "BOLTON_LLM_PROVIDER": "deterministic",
    "BOLTON_LLM_BASE_URL": "",
    "BOLTON_LLM_API_KEY": "",
    "BOLTON_LLM_MODEL": "",
    "BOLTON_ADVISER_API_TOKEN": "",
    "BOLTON_ADMIN_API_TOKEN": "",
    "ADJUST_AI_BASE_URL": "",
    "ADJUST_AI_API_KEY": "",
    "ADJUST_AI_MODEL": "",
})
sys.path.insert(0, str(ROOT / "backend"))

from fastapi import Depends, Request  # noqa: E402
from fastapi.routing import APIRoute  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.api.routes import health  # noqa: E402
from app.database.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


def hosted_health(request: Request, db: Session = Depends(get_db)):
    """Retain the original DB health probe and disclose the public demo limits."""
    return health(request, db) | {
        "public_demo": True,
        "temporary_storage": True,
        "storage_notice": "Fictional public demo. Use made-up details only. Saved records can reset or be unavailable on another server instance.",
    }


# Put only the deployment's expanded health response ahead of the original.
# Every business route, consent check and module dispatcher stays unchanged.
app.router.routes.insert(0, APIRoute("/api/health", hosted_health, methods=["GET"]))


@app.middleware("http")
async def public_demo_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Adjust-Public-Demo"] = "true"
    response.headers["X-Adjust-Persistence"] = "temporary-worker-storage"
    return response
