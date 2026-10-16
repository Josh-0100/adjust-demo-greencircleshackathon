"""Run each hosted-demo scenario in a fresh process, away from the local app.

The entrypoint intentionally sets deployment environment variables at import.
Subprocesses prevent those values and the imported host globals from leaking
into the existing backend test suite or the running local demonstration.
"""
from pathlib import Path
import os
import subprocess
import sys
import textwrap


ROOT = Path(__file__).resolve().parents[2]
PREAMBLE = """
from datetime import date, timedelta
from pathlib import Path
import json
import sqlite3
import os
from fastapi.testclient import TestClient
from api.index import app, RUNTIME_DIR, CONFIG_PATH, ROOT

STAFF = {"X-Demo-Role": "staff"}
ADMIN = {"X-Demo-Role": "admin"}
RESIDENT = {
    "text": "I used to work in retail and want to retrain for office work. I need digital skills training.",
    "resident_name": "FICTIONAL_HOSTED_RESIDENT",
    "profile": {"borough": "Bolton", "employment_status": "unemployed"},
}
"""


def isolated_scenario(body: str) -> None:
    result = subprocess.run(
        [sys.executable, "-c", PREAMBLE + textwrap.dedent(body)],
        cwd=ROOT,
        env=os.environ | {
            "DEMO_MODE": "false",
            "DATABASE_URL": "sqlite:////must-not-write/real.db",
            "LLM_PROVIDER": "compatible",
            "BOLTON_DATABASE_PATH": "/must-not-write/resident.db",
            "ADJUST_AI_BASE_URL": "https://must-not-call.invalid/v1",
        },
        text=True,
        capture_output=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cold_start_keeps_all_namespaces_and_initializes_separate_synthetic_stores():
    isolated_scenario("""
    with TestClient(app) as client:
        first = client.get("/api/health")
        assert first.status_code == 200, first.text
        assert first.json()["temporary_storage"] is True
        assert first.json()["public_demo"] is True
        assert first.json()["provider"] == "deterministic-demo"
        assert first.headers["cache-control"] == "no-store"
        assert "localhost" not in first.text
        assert client.get("/api/health").json() == first.json()
        assert client.get("/api/modules").json()["modules"]
        assert client.get("/api/bolton-connect/health").json()["provider"] == "deterministic"
        assert client.get("/api/adjust/health").json()["ai_configured"] is False
        assert len(client.get("/api/cases", headers=STAFF).json()["cases"]) == 8
        assert len(client.get("/api/bolton-connect/cases", headers=STAFF).json()["cases"]) == 6
        assert client.get("/api/cases").status_code == 403
        assert client.get("/api/bolton-connect/cases").status_code == 403
        assert Path(app.state.engine.url.database) == RUNTIME_DIR / "host.db"
        assert app.state.integration_modules.bolton_settings.database_path == RUNTIME_DIR / "resident.db"
        assert {"host.db", "resident.db", "challenge_config.yaml"} <= {p.name for p in RUNTIME_DIR.iterdir()}
        with sqlite3.connect(RUNTIME_DIR / "resident.db") as db:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "sessions" in tables and "resources" not in tables
    """)


def test_hosted_resident_consent_save_review_and_delete_remain_in_module():
    isolated_scenario("""
    with TestClient(app) as client:
        host_before = client.get("/api/cases", headers=STAFF).json()
        stats_before = client.get("/api/bolton-connect/stats", headers=STAFF).json()
        private = client.post("/api/bolton-connect/plan", json=RESIDENT)
        assert private.status_code == 200, private.text
        assert private.json()["session_id"] is None and private.json()["case_id"] is None
        assert private.json()["plan"]["recommended_services"]
        assert client.get("/api/bolton-connect/stats", headers=STAFF).json() == stats_before
        shared = client.post("/api/bolton-connect/plan", json=RESIDENT | {"consent_save": True, "consent_share": True})
        assert shared.status_code == 200, shared.text
        data = shared.json()
        assert data["session_id"] and data["case_id"]
        session_path = "/api/bolton-connect/sessions/" + data["session_id"]
        case_path = "/api/bolton-connect/cases/" + data["case_id"]
        assert client.get(session_path).json()["result"] == data["plan"]
        assert client.get(case_path).status_code == 403
        reviewed = client.patch(case_path, headers=STAFF, json={"status": "in_review", "assigned_to": "Fictional adviser"})
        assert reviewed.status_code == 200 and reviewed.json()["status"] == "in_review"
        assert RESIDENT["resident_name"] not in reviewed.text and RESIDENT["text"] not in reviewed.text
        assert client.get("/api/cases", headers=STAFF).json() == host_before
        assert client.delete(session_path).json()["deleted"] is True
        assert client.get(case_path, headers=STAFF).status_code == 404
        assert client.get("/api/bolton-connect/stats", headers=STAFF).json() == stats_before
    """)


def test_hosted_employer_journey_requires_review_and_remains_stateless():
    isolated_scenario("""
    with TestClient(app) as client:
        before = client.get("/api/bolton-connect/stats", headers=STAFF).json()
        catalogue = client.get("/api/adjust/case/catalogue")
        assert catalogue.status_code == 200 and catalogue.json()["employer_needs"]
        prepared = client.post("/api/adjust/case/prepare", json={
            "role": "employer", "description": "FICTIONAL_EMPLOYER. We need customer cover with a limited budget.",
            "support_kind": "health", "business_size": "under_50",
        })
        assert prepared.status_code == 200, prepared.text
        assert prepared.json()["status"] == "review" and "FICTIONAL_EMPLOYER" not in prepared.text
        payload = {
            "employee": {"reviewed": True, "need_ids": ["standing", "breaks"], "support_kind": "health"},
            "employer": {"reviewed": True, "need_ids": [item["id"] for item in prepared.json()["needs"]], "business_size": "under_50"},
            "review_date": (date.today() + timedelta(days=14)).isoformat(),
        }
        unreviewed = payload | {"employer": payload["employer"] | {"reviewed": False}}
        assert client.post("/api/adjust/case/plan", json=unreviewed).status_code == 422
        result = client.post("/api/adjust/case/plan", json=payload)
        assert result.status_code == 200, result.text
        assert result.json()["options"] and result.json()["conversation"]["questions"]
        assert result.headers["cache-control"] == "no-store"
        assert client.get("/api/adjust/plans").status_code == 404
        assert client.get("/api/bolton-connect/stats", headers=STAFF).json() == before
    """)


def test_admin_configuration_writes_only_the_temporary_copy():
    isolated_scenario("""
    source = ROOT / "config" / "challenge_config.yaml"
    source_before = source.read_bytes()
    assert CONFIG_PATH != source and CONFIG_PATH.read_bytes() == source_before
    with TestClient(app) as client:
        original = client.get("/api/config").json()
        payload = {"challenge": original["challenge"] | {"title": "Fictional hosted configuration"},
                   "escalation_threshold": original["escalation_threshold"]}
        response = client.put("/api/config", headers=ADMIN, json=payload)
        assert response.status_code == 200, response.text
        assert client.get("/api/config").json()["challenge"]["title"] == "Fictional hosted configuration"
        assert b"Fictional hosted configuration" in CONFIG_PATH.read_bytes()
        assert source.read_bytes() == source_before
    """)
