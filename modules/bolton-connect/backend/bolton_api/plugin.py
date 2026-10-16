"""Optional integration adapter for the host CivicForge application.

Bolton Connect runs fully standalone (``bolton_api.app:app``). This module is the
*only* bridge offered for mounting it into the host app, and it is intentionally
passive: importing it pulls in nothing from the host and nothing from the Adjust
module. A host application chooses to call ``mount_into(app)`` itself.

The manual, reviewable steps to register this module in the CivicForge module
registry and frontend are documented in ``INTEGRATION.md`` — they are never
applied automatically, so the parallel Adjust work is never touched.
"""
from __future__ import annotations

from fastapi import FastAPI

from .routes import router
from .settings import get_settings

MODULE_MANIFEST: dict = {
    "id": "bolton-connect",
    "name": "Adjust AI resident support",
    "api_prefix": "/api/bolton-connect",
    "env_prefix": "BOLTON_",
    "standalone_app": "bolton_api.app:app",
    "data_files": [
        "data/support_directory.json",
        "data/demo_residents.json",
    ],
    "owns_tables": ["sessions", "consent_events", "cases", "case_notes"],
    "touches_shared_files": False,
    "depends_on_adjust_module": False,
}


def mount_into(app: FastAPI) -> FastAPI:
    """Mount the Bolton Connect router into an existing FastAPI app.

    Safe to call from a host application. Does not register database models with
    the host ORM — this module manages its own SQLite store under ``data/``.
    """
    app.include_router(router)
    return app


def describe() -> dict:
    settings = get_settings()
    return {**MODULE_MANIFEST, "borough": settings.borough, "provider": settings.llm_provider}
