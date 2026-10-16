from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
import pytest

from adjust_api.engine import analyse, make_plan
from adjust_api.extraction import extract
from adjust_api.knowledge import KnowledgeLibrary
from adjust_api.main import create_app, scenarios
from adjust_api.models import AnalyseRequest, PlanRequest
from adjust_api.providers import ExtractedDraft, enrich, CompatibleExtractor
from adjust_api.safety import safety_check

TODAY = date(2026, 10, 16)
SCENARIOS = {item["id"]: item for item in scenarios()["scenarios"]}


def situation(id_="warehouse", **overrides):
    data = {key: SCENARIOS[id_][key] for key in ["description", "role", "constraints"]}
    return AnalyseRequest(**{**data, **overrides})


@pytest.fixture
def client():
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        yield client


def test_warehouse_extracts_tasks_and_reported_limitation_without_diagnosis():
    result = analyse(situation(), today=TODAY)
    assert result.status == "ready"
    assert {"lifting", "picking"} <= set(result.analysis.tasks)
    assert "pain" in result.analysis.reported_limitations
    assert result.analysis.role == "Warehouse picker"
    assert {r.id for r in result.recommendations} == {"handling-review", "lifting-aids", "loads-layout"}
    assert result.human_review_required and not result.data_persisted
    assert result.simulated


def test_office_scenario_retrieves_relevant_sources():
    result = analyse(situation("office"), today=TODAY)
    assert result.status == "ready"
    ids = {r.id for r in result.recommendations}
    assert {"workload", "quiet-workspace", "check-ins", "workstation"} <= ids
    assert all("lifting" not in r.id for r in result.recommendations)
    assert {"A10", "A11", "A12", "H08"} <= {s.id for s in result.sources}


def test_multiple_barriers_are_preserved():
    result = analyse(situation("multiple"), today=TODAY)
    assert {"fatigue", "stress", "mobility", "communication", "concentration"} <= set(result.analysis.scenarios)
    assert {"working-patterns", "access-layout", "workload"} <= {r.id for r in result.recommendations}


def test_vague_situation_requires_questions_before_recommending():
    result = analyse(situation("vague"), today=TODAY)
    assert result.status == "clarification" and not result.recommendations
    assert {"role", "tasks"} <= {q.id for q in result.questions if q.required}


def test_clarification_answers_complete_workflow():
    result = analyse(situation("vague", answers={"role": "Warehouse picker", "tasks": "lifting stock", "barriers": "Repeated lifting is difficult"}), today=TODAY)
    assert result.status == "ready"
    assert not result.analysis.missing_information


def test_evidence_gap_does_not_invent_an_option():
    result = analyse(situation("evidence-gap"), today=TODAY)
    assert not result.analysis.clarification_required
    assert result.status == "insufficient_evidence"
    assert result.recommendations == []
    assert result.conversation is not None


def test_no_model_network_call_by_default():
    with patch("adjust_api.providers.httpx.Client") as network:
        analyse(situation(), today=TODAY)
    network.assert_not_called()


def test_mocked_ai_may_only_fill_exact_input_excerpts():
    text = "A stock controller struggles with lifting containers."
    local = extract(AnalyseRequest(description=text))
    provider = Mock()
    provider.extract.return_value = ExtractedDraft(role="stock controller", tasks=["lifting containers"], barriers=["struggles with lifting containers"])
    outcome = enrich(local, text, True, provider)
    assert outcome.analysis.role == "stock controller"
    assert outcome.simulated is False
    assert local.role is None


@pytest.mark.parametrize("draft", [
    ExtractedDraft(role="invented manager"),
    ExtractedDraft(role="legally disabled"),
    ExtractedDraft(tasks=["x" * 241]),
    ExtractedDraft(),
])
def test_unverified_model_output_falls_back(draft):
    provider = Mock()
    provider.extract.return_value = draft
    analysis = extract(situation())
    outcome = enrich(analysis, "The employee is legally disabled. " + situation().description, True, provider)
    assert outcome.simulated
    assert outcome.analysis == analysis
    assert "unverified" in outcome.note


def test_optional_provider_failure_is_safe():
    provider = Mock()
    provider.extract.side_effect = RuntimeError("secret-provider-body")
    result = analyse(situation(use_ai=True), today=TODAY, extractor=provider)
    assert result.status == "ready" and result.simulated
    assert "secret-provider-body" not in result.model_dump_json()


def test_unsafe_optional_provider_url_cannot_make_request(monkeypatch):
    monkeypatch.setenv("ADJUST_AI_BASE_URL", "http://outside.example/v1")
    monkeypatch.setenv("ADJUST_AI_MODEL", "demo")
    with patch("adjust_api.providers.httpx.Client") as network, pytest.raises(ValueError):
        CompatibleExtractor().extract("A workplace situation")
    network.assert_not_called()


def test_guidance_catalogue_metadata_and_scenario_coverage():
    library = KnowledgeLibrary()
    assert 20 <= len(library.entries) <= 40
    assert len(library.validated(TODAY)) == len(library.entries)
    assert len({e.id for e in library.entries}) == len(library.entries)
    for entry in library.entries:
        assert entry.content_owner and entry.evidence_locator and entry.scenarios
        assert entry.last_reviewed == TODAY


@pytest.mark.parametrize("mutation", [
    {"official_url": "https://www.acas.org.uk/this-is-fabricated"},
    {"official_url": "https://www.acas.org.uk.attacker.test/reasonable-adjustments"},
    {"verification_status": "pending"}, {"verification_status": "withdrawn"},
    {"review_due": TODAY - timedelta(days=1)}, {"last_reviewed": TODAY + timedelta(days=1)},
    {"publisher": "Invented publisher"}, {"content_owner": ""},
])
def test_source_validation_fails_closed(mutation):
    library = KnowledgeLibrary()
    library.entries = [entry.model_copy(update=mutation) for entry in library.entries]
    assert library.validated(TODAY) == []
    assert analyse(situation(), library, TODAY).status == "insufficient_evidence"


def test_every_option_cites_retrieved_verified_passages():
    for id_ in SCENARIOS:
        result = analyse(situation(id_), today=TODAY)
        known = {source.id for source in result.sources}
        for rec in result.recommendations:
            assert rec.source_ids and set(rec.source_ids) <= known
            assert rec.steps and rec.employee_questions and rec.limitations and rec.referral_guidance


def test_constraints_do_not_create_workplace_barriers():
    result = extract(AnalyseRequest(description="A warehouse picker struggles with computer work at a desk.", constraints="No budget for lifting aids"))
    assert "manual" not in result.scenarios
    assert result.constraints == ["No budget for lifting aids"]


def test_explicitly_negated_health_mentions_are_not_reported_as_limitations():
    result = extract(AnalyseRequest(description="An office worker reports no anxiety or pain but struggles with computer work in a noisy room."))
    assert result.reported_limitations == []
    assert "stress" not in result.scenarios
    assert "desk" in result.scenarios


def test_no_workplace_difficulty_is_not_an_employee_barrier():
    result = analyse(AnalyseRequest(description="An office worker reports no difficulty with computer work at their desk."), today=TODAY)
    assert result.status == "clarification"
    assert "barriers" in result.analysis.missing_information


def test_long_plan_barriers_are_explicit_excerpts():
    request = plan_request(situation=situation(description="A warehouse picker struggles with repeated lifting " + "of containers " * 80))
    plan = make_plan(request, today=TODAY)
    assert all(len(barrier) <= 195 for barrier in plan.barriers)
    assert plan.barriers[0].endswith("[excerpt]")


@pytest.mark.parametrize("text", ["They are unconscious now.", "They cannot keep themselves safe.", "There is immediate danger.",
    "They say they want to kill themselves.", "They have taken an overdose.", "They are not breathing.",
    "They are trapped under a machine.", "They want to end their life.", "There is a gas leak."])
def test_immediate_danger_stops_normal_recommendations_and_ai(text):
    provider = Mock()
    result = analyse(situation(description="At the workplace: " + text, use_ai=True), today=TODAY, extractor=provider)
    assert result.status == "emergency"
    assert not result.recommendations and not result.conversation and not result.referrals
    assert "999" in result.safety.message
    provider.extract.assert_not_called()


def test_safety_checks_answers_and_constraints_too():
    result = analyse(situation(answers={"employee_view": "They cannot stay safe and need help now"}), today=TODAY)
    assert result.status == "emergency"


def test_urgent_route_and_explicit_negation():
    assert safety_check("There is a mental health crisis").level == "urgent"
    assert safety_check("There is no immediate danger. Back pain makes lifting difficult.").level == "routine"


def plan_request(**overrides):
    return PlanRequest(**{**dict(situation=situation(), selected_ids=["handling-review"], next_steps="Proposed: manager and employee to review the task this week.", review_date=TODAY + timedelta(days=14), human_reviewed=True), **overrides})


def test_plan_rebuilds_sources_and_remains_a_discussion_draft():
    plan = make_plan(plan_request(), today=TODAY)
    assert plan.status == "Discussion draft" and plan.human_reviewed
    assert plan.adjustments[0].id == "handling-review"
    assert {"H01", "H04", "H05", "A07", "A08"} <= {source.id for source in plan.sources}
    assert len(plan.external_support) == 4
    assert "not medical advice" in plan.disclaimer


@pytest.mark.parametrize("overrides", [
    {"human_reviewed": False}, {"review_date": TODAY - timedelta(days=1)},
    {"selected_ids": ["invented-advice"]}, {"situation": situation("evidence-gap")},
    {"situation": situation("vague")}, {"next_steps": "They are unconscious. Call now."},
])
def test_invalid_or_unsafe_plan_is_rejected(overrides):
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        make_plan(plan_request(**overrides), today=TODAY)


def test_bolton_service_is_not_assumed_current():
    result = analyse(situation(), today=TODAY)
    local = next(item for item in result.referrals if item.id == "bolton-workwell")
    assert local.status == "confirm_availability"
    assert "March 2026" in local.limitations


def test_api_health_and_independent_namespace(client):
    assert client.get("/api/adjust/health").json()["module"] == "adjust"
    assert client.get("/api/cases").status_code == 404
    assert client.get("/api/adjust/knowledge").json()["professional_review"] == "pending"
    assert len(client.get("/api/adjust/scenarios").json()["scenarios"]) == 5


def test_api_validates_without_echoing_sensitive_input(client):
    secret = "Private employee information " * 300
    response = client.post("/api/adjust/analyse", json={"description": secret})
    assert response.status_code == 422 and secret not in response.text
    assert "Private employee" not in response.text
    assert client.post("/api/adjust/analyse", json={"description": "too short"}).status_code == 422
    assert client.post("/api/adjust/analyse", json={"description": "This is a sufficiently long situation.", "employee_name": "X"}).status_code == 422


def test_unknown_clarification_keys_and_oversized_body_are_rejected(client):
    assert client.post("/api/adjust/analyse", json={"description": situation().description, "answers": {"diagnosis": "unknown"}}).status_code == 422
    response = client.post("/api/adjust/analyse", content=b"x" * 16001, headers={"Content-Type": "application/json"})
    assert response.status_code == 413


def test_no_cache_and_no_case_storage_endpoint(client):
    response = client.post("/api/adjust/analyse", json=situation().model_dump())
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert not response.json()["data_persisted"]
    assert client.get("/api/adjust/plans").status_code == 404
    assert client.get("/api/adjust/cases").status_code == 404


def test_api_plan_rejects_client_authored_recommendations(client):
    payload = plan_request().model_dump(mode="json")
    payload["recommendations"] = [{"title": "Invented claim"}]
    assert client.post("/api/adjust/plan", json=payload).status_code == 422


def test_no_employee_database_files_created(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client.post("/api/adjust/analyse", json=situation().model_dump())
    assert list(tmp_path.rglob("*")) == []
