"""Shared test fixtures for Bolton Connect.

The module is self-contained, so these tests import ``bolton_api`` directly from
the module's ``backend`` directory and never touch the host app or the Adjust
module. The ``client`` fixture points persistence at a throwaway SQLite file so
the real demo database is never written to.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

import pytest

# bolton_api lives under modules/bolton-connect/backend/
MODULE_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = MODULE_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from bolton_api.settings import Settings  # noqa: E402


def _load_personas() -> dict[str, dict]:
    raw = json.loads((MODULE_ROOT / "data" / "demo_residents.json").read_text(encoding="utf-8"))
    return {p["id"]: p for p in raw["residents"]}


@pytest.fixture(scope="session")
def personas() -> dict[str, dict]:
    """The six synthetic scenario personas (A–F), keyed by id."""
    return _load_personas()


@pytest.fixture
def settings() -> Settings:
    """Deterministic settings — no network, no API key."""
    return Settings(llm_provider="deterministic", demo_mode=True)


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A TestClient backed by an isolated, empty database.

    Created without the lifespan context manager so startup seeding does not
    run: every persistence test starts from a known-empty store.
    """
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("BOLTON_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("BOLTON_DEMO_MODE", "1")

    # Drop any cached store bound to a different path from a previous test.
    from bolton_api import persistence

    persistence._cached_store.cache_clear()

    from fastapi.testclient import TestClient
    from bolton_api.app import create_app

    app = create_app()
    yield TestClient(app)

    persistence._cached_store.cache_clear()
