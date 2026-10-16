from pathlib import Path
import shutil
import yaml

import pytest
from fastapi.testclient import TestClient

from app.core.settings import PROJECT_ROOT, Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path, monkeypatch):
    # Tests that construct create_app directly also use a disposable module
    # store; no suite invocation should seed a developer's resident database.
    monkeypatch.setenv("BOLTON_DATABASE_PATH", str(tmp_path / "bolton.db"))
    config = tmp_path / "challenge.yaml"
    shutil.copyfile(PROJECT_ROOT / "config" / "challenge_config.yaml", config)
    baseline = yaml.safe_load(config.read_text())
    baseline["challenge"]["borough"] = "Manchester"
    baseline["challenge"]["selected_modules"] = ["service-navigator", "employment", "community", "triage", "learning", "custom"]
    baseline["challenge"]["human_review_required"] = True
    baseline["escalation_threshold"] = 0.62
    config.write_text(yaml.safe_dump(baseline, sort_keys=False))
    return Settings(database_url=f"sqlite:///{tmp_path}/test.db", challenge_config_path=config,
                    demo_mode=True, llm_provider="deterministic", request_limit_per_minute=1000)


@pytest.fixture
def client(settings):
    database_path = settings.challenge_config_path.parent / "bolton.db"
    with TestClient(create_app(settings, bolton_settings={"database_path": database_path})) as client:
        yield client


STAFF = {"X-Demo-Role": "staff"}
ADMIN = {"X-Demo-Role": "admin"}
