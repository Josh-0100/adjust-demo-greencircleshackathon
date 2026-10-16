"""Support matching engine (Phase 5).

Deterministic, explainable matching between a resident's assessment and the
support directory. Eligibility is evaluated condition-by-condition into
ELIGIBLE / POTENTIALLY_ELIGIBLE / NOT_ELIGIBLE / UNKNOWN, and anything we cannot
evaluate becomes explicit "missing information" rather than a silent pass.

The engine never claims entitlement to a service, never auto-recommends an
unverified, expired or historical programme, and always records why a service
was suggested and what still needs checking.
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

from .directory import Directory, load_directory
from .schemas import (
    EligibilityCondition,
    EligibilityState,
    ELIGIBILITY_LABELS,
    MatchResult,
    ResidentAssessment,
    ResidentProfile,
    SourceRef,
    SupportCategory,
    SupportRecommendation,
    SupportService,
)
from .settings import Settings, get_settings

_AGE_ORDER = ["16-17", "18-24", "25-49", "50-64", "65+"]

CondResult = Literal["pass", "fail", "unknown"]


@dataclass
class _Eval:
    result: CondResult
    note: str


def _health_signalled(assessment: ResidentAssessment) -> bool:
    text = " ".join(assessment.barriers).lower()
    return any(k in text for k in ("health", "lifting", "physical", "disability", "mobility", "back"))


def _age_at_least(band: str | None, min_band: str) -> CondResult:
    if band is None or band == "prefer_not_to_say":
        return "unknown"
    try:
        return "pass" if _AGE_ORDER.index(band) >= _AGE_ORDER.index(min_band) else "fail"
    except ValueError:
        return "unknown"


def _eval_condition(
    cond: EligibilityCondition,
    profile: ResidentProfile,
    assessment: ResidentAssessment,
) -> _Eval:
    params = cond.params or {}

    if cond.kind in ("geographic", "residency"):
        boroughs = {b.lower() for b in params.get("boroughs", [])}
        areas = {a.lower() for a in params.get("areas", [])}
        borough = (profile.borough or "").strip().lower()
        if not borough:
            return _Eval("unknown", "We don't yet know which area you live in.")
        if borough in boroughs:
            return _Eval("pass", f"You live in {profile.borough}.")
        # Greater Manchester area covers Bolton and neighbouring boroughs.
        if areas and borough in {"bolton", "bury", "manchester", "oldham", "rochdale", "salford", "stockport", "tameside", "trafford", "wigan"}:
            return _Eval("pass", f"{profile.borough} is within {', '.join(params.get('areas', []))}.")
        return _Eval("fail", f"This service covers {', '.join(params.get('boroughs', []) or params.get('areas', []))}, not {profile.borough}.")

    if cond.kind == "age":
        if "bands" in params:
            allowed = set(params["bands"])
            if profile.age_band is None or profile.age_band == "prefer_not_to_say":
                return _Eval("unknown", "We don't have your age range.")
            return _Eval("pass" if profile.age_band in allowed else "fail", cond.label)
        if "min_band" in params:
            res = _age_at_least(profile.age_band, params["min_band"])
            note = cond.label if res != "unknown" else "We don't have your age range."
            return _Eval(res, note)
        return _Eval("unknown", cond.label)

    if cond.kind == "employment_status":
        allowed = set(params.get("any_of", []))
        status = assessment.employment_status
        if status == "unknown":
            return _Eval("unknown", "We don't yet know your current work situation.")
        if status in allowed:
            return _Eval("pass", cond.label)
        # A soft note means the mismatch is "not yet", not a hard exclusion.
        if params.get("note"):
            return _Eval("unknown", params["note"])
        return _Eval("fail", cond.label)

    if cond.kind == "health_or_disability":
        if profile.has_health_condition_or_disability is True:
            return _Eval("pass", "You told us about a health condition or disability affecting work.")
        if profile.has_health_condition_or_disability is False:
            return _Eval("fail", "This service is specifically for people with a health condition or disability.")
        if _health_signalled(assessment):
            return _Eval("pass", "You described a health or physical consideration affecting work.")
        return _Eval("unknown", "Whether you have a health condition or disability that affects work.")

    if cond.kind == "benefit_status":
        if profile.receives_benefits is True:
            return _Eval("pass", cond.label)
        if profile.receives_benefits is False:
            return _Eval("fail", cond.label)
        return _Eval("unknown", "Whether you currently receive benefits.")

    if cond.kind == "referral_required":
        return _Eval("unknown", "A referral is needed — an adviser can check whether this is possible for you.")

    return _Eval("unknown", cond.label)


def _aggregate(evals: list[_Eval]) -> EligibilityState:
    if not evals:
        return "eligible"
    if any(e.result == "fail" for e in evals):
        return "not_eligible"
    if all(e.result == "pass" for e in evals):
        return "eligible"
    return "potentially_eligible"


def _relevant_categories(
    assessment: ResidentAssessment, profile: ResidentProfile
) -> dict[SupportCategory, list[str]]:
    reasons: dict[SupportCategory, list[str]] = defaultdict(list)
    goals = " ".join(assessment.goals).lower()
    barriers = " ".join(assessment.barriers).lower()
    needs = " ".join(assessment.support_needs).lower()
    status = assessment.employment_status

    if status in {"unemployed", "economically_inactive"} or any(
        k in goals for k in ("return to work", "find", "flexible", "progress")
    ) or any(k in needs for k in ("cv", "interview", "job")):
        reasons["employment_assistance"].append("you're looking for work or help getting back into work")

    if assessment.training_interests or any(k in goals for k in ("retrain", "qualification")):
        reasons["skills_training"].append("you mentioned training or gaining new skills")

    if profile.digital_confidence == "low" or "digital" in barriers or any(
        "digital" in t.lower() for t in assessment.training_interests
    ):
        reasons["digital_inclusion"].append("building digital confidence could help")

    if profile.has_health_condition_or_disability or _health_signalled(assessment):
        reasons["disability_employment_support"].append(
            "you described a health or physical consideration affecting work"
        )
        reasons["workplace_adjustments"].append("adjustments at work might help you stay in or start a role")

    if profile.receives_benefits or any(k in barriers for k in ("money", "transport")) or any(
        k in needs for k in ("benefit", "money", "transport")
    ):
        reasons["financial_guidance"].append("you mentioned money, benefits or transport costs")

    if "confidence" in barriers or "confidence" in needs or "wellbeing" in barriers:
        reasons["wellbeing_support"].append("you mentioned confidence or wellbeing")
        reasons["community_support"].append("connecting with others locally may help your confidence")

    return reasons


def _build_recommendation(
    service: SupportService,
    category_reasons: list[str],
    profile: ResidentProfile,
    assessment: ResidentAssessment,
) -> SupportRecommendation:
    evals = [_eval_condition(c, profile, assessment) for c in service.eligibility]
    state = _aggregate(evals)

    reasons = list(category_reasons)
    reasons.extend(e.note for e in evals if e.result == "pass")
    missing = [e.note for e in evals if e.result == "unknown"]

    caveats: list[str] = []
    next_steps: list[str] = []

    if not service.active or service.verification_status in {"expired", "historical"}:
        caveats.append("This programme is closed or no longer running — it is shown for context only.")
    elif not service.auto_recommendable:
        caveats.append("Details are unverified — confirm this service is available before relying on it.")
    if service.synthetic:
        caveats.append("Demonstration service — this is not a real listing.")

    for note in service.notes:
        caveats.append(note)
    for req in service.referral_requirements:
        next_steps.append(req)

    contact = service.public_contact()
    if contact:
        next_steps.append(f"Contact: {contact}")
    elif service.source_url:
        next_steps.append(f"Find out more: {service.source_url}")

    auto = service.auto_recommendable and state in {"eligible", "potentially_eligible"}

    why = service.description
    if category_reasons:
        why = f"{service.description} Suggested because {category_reasons[0]}."
    why = why[:600]

    return SupportRecommendation(
        service_id=service.id,
        name=service.name,
        provider=service.provider,
        category=service.category,
        eligibility_state=state,
        eligibility_label=ELIGIBILITY_LABELS[state],
        why_it_helps=why,
        reasons=reasons[:20],
        missing_information=missing[:20],
        next_steps=next_steps[:12],
        caveats=caveats[:12],
        auto_recommended=auto,
        source=SourceRef(
            label=service.source_label,
            url=service.source_url,
            last_verified=service.last_verified,
            verification_status=service.verification_status,
            synthetic=service.synthetic,
        ),
    )


_STATE_RANK = {"eligible": 0, "potentially_eligible": 1, "unknown": 2, "not_eligible": 3}


def match(
    assessment: ResidentAssessment,
    profile: ResidentProfile | None = None,
    settings: Settings | None = None,
    directory: Directory | None = None,
    limit: int = 8,
) -> MatchResult:
    """Match a resident assessment to support services."""
    started = time.perf_counter()
    settings = settings or get_settings()
    profile = profile or ResidentProfile()
    directory = directory or load_directory(settings)

    # With too little information we do not assert any match.
    if assessment.clarification_required:
        return MatchResult(
            assessment=assessment,
            recommendations=[],
            needs_human_review=True,
            review_reasons=["Not enough information yet — a clarifying question was asked before matching."],
            safety_notes=["No services were matched because the assessment was too thin to do so responsibly."],
            provider=assessment.provider,
            processing_ms=int((time.perf_counter() - started) * 1000),
        )

    category_reasons = _relevant_categories(assessment, profile)

    recs: list[SupportRecommendation] = []
    for service in directory.all():
        reasons = category_reasons.get(service.category, [])
        # Include a service if its category is relevant, or if it is a general
        # employment route for someone looking for work.
        if not reasons and service.category != "employment_assistance":
            continue
        if not reasons and assessment.employment_status not in {"unemployed", "economically_inactive", "unknown"}:
            continue
        recs.append(_build_recommendation(service, reasons, profile, assessment))

    recs.sort(
        key=lambda r: (
            not r.auto_recommended,
            _STATE_RANK.get(r.eligibility_state, 2),
            r.source.verification_status != "verified",
            -len(r.reasons),
        )
    )
    recs = recs[:limit]

    review_reasons = ["All AI-assisted matches should be checked by a human adviser before action."]
    safety_notes: list[str] = []
    if any(not r.auto_recommended for r in recs):
        safety_notes.append(
            "Some services are shown with a 'confirm availability' caveat and are not automatic recommendations."
        )
    if any(r.source.synthetic for r in recs):
        safety_notes.append("Some entries are clearly-labelled demonstration data, not real services.")

    return MatchResult(
        assessment=assessment,
        recommendations=recs,
        needs_human_review=True,
        review_reasons=review_reasons,
        safety_notes=safety_notes,
        provider=assessment.provider,
        processing_ms=int((time.perf_counter() - started) * 1000),
    )
