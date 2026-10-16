import json

import httpx
import pytest
from pydantic import ValidationError

from app.ai.providers import CompatibleProvider
from app.ai.tools import TOOLS
from app.evaluation.benchmark import FIXTURES, run_benchmark
from app.modules.base import extract_skills


def test_labelled_synthetic_fixture_evaluation(client):
    with client.app.state.session_factory() as db:
        report = run_benchmark(db, client.app.state.settings)
    assert report["fixture_count"] == 12
    assert report["category_accuracy"] == 1, report
    assert report["expected_source_recall"] == 1, report
    assert report["grounded_recommendation_rate"] == 1, report


def test_skills_extraction_does_not_claim_a_negated_or_future_skill():
    assert "spreadsheets" not in extract_skills("I have customer service experience but no spreadsheets experience.")
    assert "spreadsheets" not in extract_skills("I need to learn spreadsheets for office work.")
    assert {"communication", "digital literacy"}.issubset(extract_skills("I have customer service and email experience."))
    assert "spreadsheets" in extract_skills("I have experience using Excel.")


def test_typed_tool_registry_rejects_unapproved_actions_and_args(client):
    with client.app.state.session_factory() as db:
        with pytest.raises(ValueError):
            TOOLS.invoke("approve_eligibility", {}, db)
        with pytest.raises(ValidationError):
            TOOLS.invoke("retrieve_approved_resources", {"message":"Find housing support", "borough":"London", "module_ids":["triage"]}, db)


def mock_response(content):
    return httpx.Response(200, request=httpx.Request("POST", "https://example.org/v1/chat/completions"),
                          json={"choices":[{"message":{"content":json.dumps(content)}}]})


@pytest.mark.parametrize("invalid", [
    {"summary":"The resident is eligible for a £500 council housing grant.", "source_ids":[1]},
    {"summary":"My home is cold and I need support.", "source_ids":[999]},
    {"summary":"My home is cold and I need support.", "source_ids":[1], "extra":"arbitrary instruction"},
])
def test_optional_provider_rejects_invented_or_unstructured_results(settings, monkeypatch, invalid):
    settings = settings.model_copy(update={"llm_provider":"compatible", "llm_base_url":"https://example.org/v1", "llm_model":"test-model", "llm_api_key":"not-a-real-key"})
    monkeypatch.setattr(httpx.Client, "post", lambda *args, **kwargs: mock_response(invalid))
    result = CompatibleProvider(settings).annotate("My home is cold and I need support.", [{"resource_id":1, "excerpt":"Synthetic home-support pathway."}], "Safe deterministic summary")
    assert result.provider == "deterministic-demo"
    assert result.summary == "Safe deterministic summary"
    assert result.fallback_note and "not-a-real-key" not in result.fallback_note


def test_optional_provider_accepts_only_exact_resident_excerpt(settings, monkeypatch):
    settings = settings.model_copy(update={"llm_provider":"compatible", "llm_base_url":"https://example.org/v1", "llm_model":"test-model", "llm_api_key":"not-a-real-key"})
    monkeypatch.setattr(httpx.Client, "post", lambda *args, **kwargs: mock_response({"summary":"My home is cold", "source_ids":[1]}))
    result = CompatibleProvider(settings).annotate("My home is cold and I need support.", [{"resource_id":1}], "Safe deterministic summary")
    assert result.provider == "compatible:test-model" and "extracted quote" in result.summary
    assert result.simulated is False


def test_provider_outage_preserves_workflow(settings, monkeypatch):
    settings = settings.model_copy(update={"llm_provider":"compatible", "llm_base_url":"https://example.org/v1", "llm_model":"test-model", "llm_api_key":"not-a-real-key"})
    def timeout(*args, **kwargs):
        raise httpx.ReadTimeout("Simulated provider timeout")
    monkeypatch.setattr(httpx.Client, "post", timeout)
    result = CompatibleProvider(settings).annotate("My home is cold and I need support.", [{"resource_id":1}], "Safe deterministic summary")
    assert result.summary == "Safe deterministic summary" and result.provider == "deterministic-demo"
