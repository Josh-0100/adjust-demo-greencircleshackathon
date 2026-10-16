"""Phase 9 — the six required demonstration scenarios (A–F).

Each test drives the real deterministic pipeline end to end for one synthetic
persona and asserts the behaviour the brief calls for: correct understanding,
no invented entitlements, practical limitations (never a medical diagnosis),
and closed/time-limited programmes that are never auto-recommended.
"""
from __future__ import annotations

from bolton_api.action_plan import build_action_plan
from bolton_api.assessment import assess
from bolton_api.matching import match
from bolton_api.pathways import generate_pathways
from bolton_api.schemas import AssessmentRequest, ResidentProfile


def run_pipeline(persona: dict, settings):
    profile = ResidentProfile(**persona.get("profile", {}))
    request = AssessmentRequest(text=persona["text"], profile=profile)
    assessment = assess(request, settings)
    result = match(assessment, profile, settings)
    pathways = generate_pathways(assessment, settings)
    plan = build_action_plan(
        assessment, result, pathways, profile,
        resident_name=persona.get("name", "Resident"), settings=settings,
    )
    return assessment, result, pathways, plan


def rec_by_id(result, service_id):
    return next((r for r in result.recommendations if r.service_id == service_id), None)


# --- Scenario A — clear case with a practical limitation --------------------

def test_scenario_a_clear_case(personas, settings):
    assessment, result, _pathways, plan = run_pipeline(personas["demo-a"], settings)

    assert assessment.employment_status == "unemployed"
    assert "warehouse" in assessment.experience
    assert assessment.goals, "a return-to-work goal should be captured"
    assert not assessment.clarification_required

    # Practical limitation is recorded as the resident phrased it, never as a
    # medical diagnosis or a fitness-for-work judgement.
    joined = " ".join(assessment.barriers).lower()
    assert "heavy lifting" in joined
    for diagnosis_word in ("diagnosis", "unfit", "incapable", "cannot work"):
        assert diagnosis_word not in joined

    hub = rec_by_id(result, "bolton-employment-hub")
    assert hub is not None and hub.eligibility_state == "eligible"
    assert hub.auto_recommended is True
    assert result.needs_human_review is True

    # Inferred strengths must be labelled as AI suggestions, not stated facts.
    assert plan.strengths, "strengths section should be populated"
    assert all(s.provenance == "ai_suggestion" for s in plan.strengths)


# --- Scenario B — too little information, needs a clarifying question --------

def test_scenario_b_needs_clarification(personas, settings):
    assessment, result, pathways, _plan = run_pipeline(personas["demo-b"], settings)

    assert assessment.clarification_required is True
    assert assessment.clarifying_question and assessment.clarifying_question.strip()
    # With too little to go on we must not fabricate matches or pathways.
    assert result.recommendations == []
    assert result.review_reasons
    assert pathways == []


# --- Scenario C — career changer wanting to retrain -------------------------

def test_scenario_c_retrain(personas, settings):
    assessment, result, pathways, _plan = run_pipeline(personas["demo-c"], settings)

    assert not assessment.clarification_required
    assert any("retrain" in g.lower() or "new sector" in g.lower() for g in assessment.goals)
    assert "Digital skills" in assessment.training_interests
    assert any("face-to-face" in p.lower() for p in assessment.support_preferences)

    # A local training/skills route should surface for a retrainer.
    rec_ids = {r.service_id for r in result.recommendations}
    assert {"bolton-college-adult-skills", "learn-my-way"} & rec_ids
    assert pathways, "a retrainer should get at least one exploration pathway"


# --- Scenario D — returning carer who has lost confidence -------------------

def test_scenario_d_returning_carer(personas, settings):
    assessment, _result, _pathways, _plan = run_pipeline(personas["demo-d"], settings)

    # Regression guard: "lost my confidence" must not be read as job loss.
    # The profile states economically_inactive and that must stand.
    assert assessment.employment_status == "economically_inactive"
    assert not assessment.clarification_required
    needs = " ".join(assessment.support_needs).lower()
    assert "cv" in needs
    assert any("confidence" in b.lower() for b in assessment.barriers)


# --- Scenario E — health condition, in work, wants adjustments --------------

def test_scenario_e_health_adjustments(personas, settings):
    assessment, result, pathways, _plan = run_pipeline(personas["demo-e"], settings)

    assert assessment.employment_status == "employed"
    assert assessment.barriers, "a health-related consideration should be recorded"

    # Workplace-adjustment support should be offered; a health condition must
    # never be used to withhold or exclude opportunities.
    ata = rec_by_id(result, "access-to-work")
    assert ata is not None and ata.auto_recommended is True
    for pathway in pathways:
        caveats = " ".join(pathway.caveats).lower()
        if caveats:
            assert "not a barrier" in caveats


# --- Scenario F — would match a time-limited / closed programme -------------

def test_scenario_f_closed_programme_never_auto(personas, settings):
    assessment, result, _pathways, _plan = run_pipeline(personas["demo-f"], settings)

    assert assessment.employment_status == "unemployed"

    kickstart = rec_by_id(result, "kickstart-scheme-historical")
    assert kickstart is not None, "the closed scheme should still surface for context"
    # The crucial guarantee: even though this young UC claimant *matches* the
    # scheme's original eligibility, a closed programme is never auto-recommended
    # and must carry a caveat explaining it is no longer available.
    assert kickstart.auto_recommended is False
    assert any(
        "closed" in c.lower() or "no longer" in c.lower() or "expired" in c.lower()
        for c in kickstart.caveats
    )
