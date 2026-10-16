"""Exercise real child applications across their composition boundaries."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import inspect

from app.main import create_app
from tests.conftest import STAFF


RESIDENT = {
    "text": "I used to work in retail and want to retrain for office work. I need digital skills training.",
    "resident_name": "PRIVATE_RESIDENT_ALPHA",
    "profile": {"borough": "Bolton", "employment_status": "unemployed"},
}


def test_real_apps_keep_namespaces_complete_routes_and_startup(client):
    assert client.get("/api/health").json()["status"] == "ok"
    assert client.get("/api/bolton-connect/health").json()["module"] == "bolton-connect"
    assert client.get("/api/adjust/health").json()["module"] == "adjust"
    assert client.get("/api/adjust/case/catalogue").json()["employee_needs"]
    assert len(client.get("/api/bolton-connect/cases", headers=STAFF).json()["cases"]) == 6
    assert len(client.get("/api/cases", headers=STAFF).json()["cases"]) == 8
    assert client.get("/api/adjustment/health").status_code == 404
    assert client.get("/api/bolton-connected/health").status_code == 404


def test_stores_and_schemas_stay_independent(client):
    module = client.app.state.integration_modules
    module_path = module.bolton_settings.database_path
    host_path = Path(client.app.state.engine.url.database)
    assert module_path.resolve() != host_path.resolve()
    with sqlite3.connect(module_path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"sessions", "consent_events", "cases", "case_notes"} <= tables
    assert "alembic_version" not in tables and "resources" not in tables
    assert "sessions" not in inspect(client.app.state.engine).get_table_names()


def test_resident_consent_resume_review_and_erase_do_not_transfer_to_other_apps(client):
    initial_stats = client.get("/api/bolton-connect/stats", headers=STAFF).json()
    host_before = client.get("/api/cases", headers=STAFF).json()
    private = client.post("/api/bolton-connect/plan", json=RESIDENT)
    assert private.status_code == 200
    assert private.json()["session_id"] is None and private.json()["case_id"] is None
    assert private.json()["plan"]["recommended_services"]
    assert client.get("/api/bolton-connect/stats", headers=STAFF).json() == initial_stats

    saved = client.post("/api/bolton-connect/plan", json=RESIDENT | {"consent_save": True}).json()
    assert saved["session_id"] and saved["case_id"] is None
    shared = client.post("/api/bolton-connect/plan", json=RESIDENT | {"consent_save": True, "consent_share": True}).json()
    assert shared["session_id"] and shared["case_id"]
    assert client.get(f"/api/bolton-connect/sessions/{shared['session_id']}").json()["result"] == shared["plan"]
    assert client.get(f"/api/bolton-connect/cases/{shared['case_id']}").status_code == 403
    reviewed = client.patch(f"/api/bolton-connect/cases/{shared['case_id']}", headers=STAFF,
                            json={"status": "in_review", "assigned_to": "Synthetic adviser"})
    assert reviewed.status_code == 200 and reviewed.json()["status"] == "in_review"
    assert RESIDENT["resident_name"] not in reviewed.text and RESIDENT["text"] not in reviewed.text
    assert client.get("/api/cases", headers=STAFF).json() == host_before
    assert client.get("/api/adjust/cases").status_code == 404
    for session in (saved["session_id"], shared["session_id"]):
        assert client.delete(f"/api/bolton-connect/sessions/{session}").json()["deleted"] is True
    assert client.get(f"/api/bolton-connect/cases/{shared['case_id']}", headers=STAFF).status_code == 404
    assert client.get("/api/bolton-connect/stats", headers=STAFF).json() == initial_stats


def test_adjust_current_two_sided_journey_retains_review_and_privacy(client):
    before = client.get("/api/bolton-connect/stats", headers=STAFF).json()
    prepared = client.post("/api/adjust/case/prepare", json={
        "role": "employer", "description": "PRIVATE_EMPLOYER_BETA. We need customer cover with a limited budget.",
        "support_kind": "health", "business_size": "under_50",
    })
    assert prepared.status_code == 200 and prepared.json()["status"] == "review"
    assert "PRIVATE_EMPLOYER_BETA" not in prepared.text
    needs = [item["id"] for item in prepared.json()["needs"]]
    request = {
        "employee": {"reviewed": True, "need_ids": ["standing", "breaks"], "support_kind": "health"},
        "employer": {"reviewed": True, "need_ids": needs, "business_size": "under_50"},
        "review_date": (date.today() + timedelta(days=14)).isoformat(),
    }
    unreviewed = request | {"employer": request["employer"] | {"reviewed": False}}
    assert client.post("/api/adjust/case/plan", json=unreviewed).status_code == 422
    plan = client.post("/api/adjust/case/plan", json=request)
    assert plan.status_code == 200 and plan.json()["options"]
    assert plan.headers["cache-control"] == "no-store"
    assert client.get("/api/bolton-connect/stats", headers=STAFF).json() == before
    assert client.get("/api/adjust/plans").status_code == 404


def test_production_host_identity_overrides_module_demo_settings_and_tokens(settings, monkeypatch):
    monkeypatch.setenv("BOLTON_DEMO_MODE", "true")
    monkeypatch.setenv("BOLTON_ADVISER_API_TOKEN", "old-module-token")
    secure = settings.model_copy(update={"demo_mode": False, "staff_api_token": "s" * 30, "admin_api_token": "a" * 30})
    app = create_app(secure, bolton_settings={"database_path": settings.challenge_config_path.parent / "secure.db", "demo_mode": True})
    with TestClient(app) as live:
        assert live.get("/api/bolton-connect/health").json()["demo_mode"] is False
        for path in ("/api/cases", "/api/bolton-connect/cases", "/api/bolton-connect/stats"):
            assert live.get(path, headers={"X-Demo-Role": "admin"}).status_code == 403
            assert live.get(path, headers={"Authorization": "Bearer " + "s" * 30}).status_code == 200
            assert live.get(path, headers={"Authorization": "Bearer " + "a" * 30}).status_code == 200
        assert live.get("/api/bolton-connect/cases", headers={"Authorization": "Bearer old-module-token"}).status_code == 403
        assert live.get("/api/bolton-connect/cases", headers={"Authorization": "Bearer " + "s" * 30}).json()["cases"] == []


@pytest.mark.parametrize("module,route,limit", [
    ("bolton-connect", "plan", 60000), ("adjust", "case/prepare", 16000),
])
def test_child_body_limits_work_without_content_length_and_errors_do_not_echo(client, module, route, limit):
    private = "PRIVATE_ERROR_GAMMA " * 230
    payload = {"text": private} if module == "bolton-connect" else {"role": "employer", "description": private}
    response = client.post(f"/api/{module}/{route}", json=payload)
    assert response.status_code == 422 and "PRIVATE_ERROR_GAMMA" not in response.text
    assert response.headers["cache-control"] == "no-store"
    oversized = client.post(f"/api/{module}/{route}", content=iter([b"x" * 9000] * (limit // 9000 + 1)),
                            headers={"Content-Type": "application/json"})
    assert oversized.status_code == 413
    assert oversized.headers["cache-control"] == "no-store"


def test_module_requests_do_not_spend_original_host_rate_budget(settings):
    limited = settings.model_copy(update={"request_limit_per_minute": 2})
    app = create_app(limited, bolton_settings={"database_path": settings.challenge_config_path.parent / "rate.db"})
    with TestClient(app) as client:
        for _ in range(3):
            assert client.get("/api/bolton-connect/health").status_code == 200
            assert client.get("/api/adjust/health").status_code == 200
        assert client.get("/api/config").status_code == 200
        assert client.get("/api/modules").status_code == 200
        assert client.get("/api/config").status_code == 429


@pytest.mark.parametrize("symlink", [False, True])
def test_host_store_alias_is_rejected_before_startup(settings, symlink):
    path = Path(settings.database_url.removeprefix("sqlite:///"))
    if symlink:
        path.touch()
        alias = path.with_name("linked.db")
        alias.symlink_to(path)
    else:
        alias = path
    with pytest.raises(ValueError, match="separate database"):
        create_app(settings, bolton_settings={"database_path": alias})


def test_simultaneous_hosts_do_not_share_module_settings_or_credentials(settings):
    second = settings.model_copy(update={"demo_mode": False, "staff_api_token": "s" * 30, "admin_api_token": "a" * 30,
                                        "database_url": f"sqlite:///{settings.challenge_config_path.parent}/second-host.db"})
    first_app = create_app(settings, bolton_settings={"database_path": settings.challenge_config_path.parent / "first-module.db"})
    second_app = create_app(second, bolton_settings={"database_path": settings.challenge_config_path.parent / "second-module.db"})
    with TestClient(first_app) as demo, TestClient(second_app) as secure:
        def read(client):
            return client.get("/api/bolton-connect/health").json()["demo_mode"], client.get("/api/bolton-connect/cases", headers=STAFF).status_code
        with ThreadPoolExecutor(max_workers=2) as workers:
            demo_result, secure_result = list(workers.map(read, (demo, secure)))
        assert demo_result == (True, 200)
        assert secure_result == (False, 403)
        assert len(demo.get("/api/bolton-connect/cases", headers=STAFF).json()["cases"]) == 6
        assert secure.get("/api/bolton-connect/cases", headers={"Authorization": "Bearer " + "s" * 30}).json()["cases"] == []


def test_static_module_document_and_delete_preflight_are_available(client):
    document = client.get("/module-assets/bolton-connect/")
    assert document.status_code == 200 and 'id="assess-form"' in document.text
    assert client.get("/module-assets/bolton-connect/app.js").status_code == 200
    response = client.options("/api/bolton-connect/sessions/example", headers={
        "Origin": "http://localhost:3000", "Access-Control-Request-Method": "DELETE",
    })
    assert response.status_code == 200


def test_unexpected_module_failure_is_redacted_and_other_apps_remain_available(client, monkeypatch):
    def fail(settings):
        raise RuntimeError("PRIVATE_EXCEPTION_DELTA")
    monkeypatch.setattr("bolton_api.routes.load_directory", fail)
    # The fixture already entered the host/module lifespans. Production ASGI
    # servers return the response from the exception handler and log the error.
    response = TestClient(client.app, raise_server_exceptions=False).get("/api/bolton-connect/health")
    assert response.status_code == 503 and "PRIVATE_EXCEPTION_DELTA" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/adjust/health").status_code == 200
