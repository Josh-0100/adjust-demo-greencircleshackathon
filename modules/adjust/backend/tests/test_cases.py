"""Two-sided contracts, privacy and substantive safety/constraint invariants."""
from copy import deepcopy
from datetime import date, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from adjust_api.cases import CombinedPlanRequest, make_combined_plan
from adjust_api.main import create_app

BASE = "/api/adjust/case"
TODAY = date(2026, 10, 16)


@pytest.fixture
def client():
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        yield client


def prepared(role="employee", **overrides):
    return {"role": role, "description": "Mornings and long periods of standing are difficult at work.",
            "support_kind": "health", "business_size": None, "role_context": "", "practicalities": "", "tried": "", **overrides}


def joint(**overrides):
    return {"employee": {"reviewed": True, "need_ids": ["later-start", "breaks"], "support_kind": "health"},
            "employer": {"reviewed": True, "need_ids": ["cover"], "business_size": "under_50"},
            "review_date": (date.today() + timedelta(days=14)).isoformat(), **overrides}


def test_catalogue_contains_authored_needs_only(client):
    response = client.get(BASE + "/catalogue")
    assert response.status_code == 200
    data = response.json()
    assert {n["id"] for n in data["employee_needs"]} == {"later-start", "breaks", "standing", "lifting", "quiet", "written", "workload", "flexibility", "appointments", "discuss-needs"}
    assert {n["id"] for n in data["employer_needs"]} == {"cover", "core-tasks", "fixed-hours", "limited-budget", "small-space", "tried-flexible", "discuss-practicalities"}
    assert response.headers["cache-control"] == "no-store"


def test_prepare_never_echoes_employee_description_or_medical_details(client):
    private = "Fictional person ALPHA_PRIVATE has multiple sclerosis. Mornings are hard and repeated lifting is difficult."
    response = client.post(BASE + "/prepare", json=prepared(description=private))
    assert response.status_code == 200
    assert response.json()["status"] == "review"
    assert {n["id"] for n in response.json()["needs"]} == {"later-start", "lifting"}
    assert private not in response.text and "ALPHA_PRIVATE" not in response.text and "multiple sclerosis" not in response.text


def test_employer_prepare_uses_all_practical_fields_without_sharing_words(client):
    response = client.post(BASE + "/prepare", json=prepared("employer", description="The business has limited space and a limited budget.", role_context="Core duties and fixed hours are essential.", practicalities="We need customer cover.", tried="We tried flexible shifts. BETA_PRIVATE"))
    assert response.status_code == 200
    assert {n["id"] for n in response.json()["needs"]} == {"small-space", "limited-budget", "core-tasks", "fixed-hours", "cover", "tried-flexible"}
    assert "BETA_PRIVATE" not in response.text


@pytest.mark.parametrize("context", [
    "Customer cover is needed during fixed opening hours.",
    "This job has fixed working hours.",
    "We cannot change shifts in this role.",
    "Opening hours cannot change for the shop.",
])
def test_fixed_opening_working_hours_and_shifts_are_reviewed_constraints(client, context):
    response = client.post(BASE + "/prepare", json=prepared("employer", description="We would like to talk about what is practical in the workplace.", role_context=context))
    assert response.status_code == 200
    assert "fixed-hours" in {item["id"] for item in response.json()["needs"]}


@pytest.mark.parametrize("role", ["employee", "employer"])
@pytest.mark.parametrize("field", ["description", "role_context", "practicalities", "tried"])
def test_crisis_in_every_private_field_stops_both_flows(client, role, field):
    payload = prepared(role, **{field: "They cannot keep themselves safe and need immediate help now."})
    response = client.post(BASE + "/prepare", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "emergency"
    assert response.json()["needs"] == []
    assert all(route in response.text for route in ["999", "111", "116 123"])


def test_urgent_flow_has_all_support_routes(client):
    response = client.post(BASE + "/prepare", json=prepared(description="There is an urgent mental health crisis at work today."))
    assert response.json()["status"] == "urgent"
    assert response.json()["needs"] == []
    assert all(route in response.text for route in ["999", "111", "116 123"])


@pytest.mark.parametrize("text", [
    "I am thinking about ending my life because things feel impossible.",
    "I feel like ending it all and I need help with what is happening.",
    "I might hurt myself and I do not know how to manage work.",
    "I don't want to live anymore and everything feels too hard.",
    "I have a plan to take my own life and need help now.",
    "I can't go on and I feel overwhelmed by everything.",
])
def test_case_safety_stops_for_first_person_crisis_phrases(client, text):
    response = client.post(BASE + "/prepare", json=prepared(description=text))
    assert response.json()["status"] in {"urgent", "emergency"}
    assert response.json()["needs"] == []
    assert all(route in response.text for route in ["999", "111", "116 123"])
    assert response.json()["safety"]["official_url"].startswith("https://www.nhs.uk/")
    if "can't go on" in text:
        assert response.json()["status"] == "urgent"


def test_case_safety_preserves_explicitly_negated_suicidal_thoughts(client):
    response = client.post(BASE + "/prepare", json=prepared(description="Fictional example: I had no suicidal thoughts. Standing at work makes me tired."))
    assert response.json()["status"] == "review"
    assert response.json()["needs"]


@pytest.mark.parametrize("role,id_", [("employee", "discuss-needs"), ("employer", "discuss-practicalities")])
def test_unknown_barriers_get_general_review_instead_of_unsupported_advice(client, role, id_):
    response = client.post(BASE + "/prepare", json=prepared(role, description="There is a specialist situation we need to talk about."))
    assert [n["id"] for n in response.json()["needs"]] == [id_]


@pytest.mark.parametrize("side", ["employee", "employer"])
def test_plan_requires_both_reviewed_contributions(client, side):
    missing = joint()
    del missing[side]
    assert client.post(BASE + "/plan", json=missing).status_code == 422
    unreviewed = joint()
    unreviewed[side]["reviewed"] = False
    assert client.post(BASE + "/plan", json=unreviewed).status_code == 422


def test_plan_accepts_removing_every_need_and_still_uses_both_sides(client):
    data = joint()
    data["employee"]["need_ids"] = []
    data["employer"]["need_ids"] = []
    response = client.post(BASE + "/plan", json=data)
    assert response.status_code == 200
    assert "No employee needs have been included" in response.text
    assert "practical for the business" in response.text


@pytest.mark.parametrize("side,ids", [("employee", ["private condition name"]), ("employer", ["later-start"]), ("employee", ["breaks", "breaks"]), ("employee", ["breaks"] * 11)])
def test_plan_rejects_unknown_cross_role_and_duplicate_ids(client, side, ids):
    data = joint()
    data[side]["need_ids"] = ids
    response = client.post(BASE + "/plan", json=data)
    assert response.status_code == 422
    assert "private condition name" not in response.text


@pytest.mark.parametrize("extra", ["description", "medical_details", "private_words", "options"])
def test_raw_text_or_client_authored_options_cannot_enter_plan(client, extra):
    payload = joint(**{extra: "PRIVATE_GAMMA"})
    response = client.post(BASE + "/plan", json=payload)
    assert response.status_code == 422 and "PRIVATE_GAMMA" not in response.text
    nested = joint()
    nested["employee"][extra] = "PRIVATE_GAMMA"
    assert client.post(BASE + "/plan", json=nested).status_code == 422


def test_fixed_hours_prevents_start_time_proposal_and_asks_about_constraint(client):
    open_plan = client.post(BASE + "/plan", json=joint()).json()
    payload = joint()
    payload["employer"]["need_ids"] = ["fixed-hours", "tried-flexible", "limited-budget"]
    constrained = client.post(BASE + "/plan", json=payload).json()
    assert "agreed-start" in {item["id"] for item in open_plan["start_now"]}
    assert "agreed-start" not in {item["id"] for item in constrained["start_now"]}
    assert any("within those hours" in text for text in constrained["conversation"]["questions"])
    assert any("previous flexible" in text for text in constrained["conversation"]["questions"])
    assert any("limited budget" in text for text in constrained["conversation"]["questions"])


def test_lifting_option_requires_assessment_not_an_unsafe_lifting_instruction(client):
    payload = joint()
    payload["employee"]["need_ids"] = ["lifting"]
    plan = client.post(BASE + "/plan", json=payload).json()
    option = next(option for option in plan["options"] if option["id"] == "safe-handling")
    assert option["url"].startswith("https://www.hse.gov.uk/")
    assert "competent task assessment" in option["detail"]
    assert "do not assume" in option["detail"]


@pytest.mark.parametrize("size,expected", [("under_50", "nil employer cost share"), ("50_249", "£500 threshold"), ("250_plus", "£1,000 threshold")])
def test_access_to_work_is_qualified_and_specific_to_employer_size(client, size, expected):
    data = joint()
    data["employer"]["business_size"] = size
    plan = client.post(BASE + "/plan", json=data).json()
    funding = next(item for item in plan["help"] if item["id"] == "access-to-work")
    assert expected in funding["detail"]
    assert "no award is guaranteed" in funding["detail"]
    assert "Statutory reasonable adjustments are not funded" in funding["detail"]
    assert "confirm the actual award" in funding["detail"]


@pytest.mark.parametrize("support_kind", ["carer", "both"])
def test_carers_get_all_four_verified_rights_and_distinct_adjustment_note(client, support_kind):
    data = joint()
    data["employee"] = {"reviewed": True, "need_ids": ["flexibility"], "support_kind": support_kind}
    plan = client.post(BASE + "/plan", json=data).json()
    assert {"flexible-working", "carers-leave"} <= {x["id"] for x in plan["options"]}
    assert {"carer-assessment", "carers-allowance"} <= {x["id"] for x in plan["help"]}
    assert "right to request" in next(x["detail"] for x in plan["options"] if x["id"] == "flexible-working")
    assert "unpaid" in next(x["detail"] for x in plan["options"] if x["id"] == "carers-leave")
    assert "Caring alone does not create" in plan["legal_note"]
    if support_kind == "carer":
        assert "Caring alone does not establish eligibility" in next(x["detail"] for x in plan["help"] if x["id"] == "access-to-work")


def test_review_date_must_be_future(client):
    for day in [date.today(), date.today() - timedelta(days=1)]:
        assert client.post(BASE + "/plan", json=joint(review_date=day.isoformat())).status_code == 422


def test_plan_is_deterministic_without_network_or_persistence(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = joint()
    with patch("httpx.Client.send") as network:
        # Call the pure operation: mocking HTTPX's transport would also prevent
        # TestClient from making its in-process API request.
        first = make_combined_plan(CombinedPlanRequest(**deepcopy(data)), today=TODAY)
        second = make_combined_plan(CombinedPlanRequest(**deepcopy(data)), today=TODAY)
    network.assert_not_called()
    assert first == second
    assert list(tmp_path.rglob("*")) == []
    assert all(item.url.startswith("https://") for item in [*first.start_now, *first.options, *first.help])
    assert "Fictional demo" in first.disclaimer
    assert client.get(BASE + "/sessions").status_code == 404


def test_invalid_prepare_does_not_echo_any_private_field(client):
    secret = "PRIVATE_DELTA " * 700
    response = client.post(BASE + "/prepare", json=prepared(description=secret))
    assert response.status_code == 422 and "PRIVATE_DELTA" not in response.text
    assert client.post(BASE + "/prepare", json=prepared(description="short")).status_code == 422
