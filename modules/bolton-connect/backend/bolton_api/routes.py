"""HTTP API for Bolton Connect (namespace ``/api/bolton-connect``).

Resident endpoints are open in demo mode; adviser/admin endpoints require the
``staff`` role (an ``X-Demo-Role`` header in demo mode, or a bearer token
otherwise). Nothing here integrates with the Adjust module.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import Field, field_validator

from .assessment import assess
from .action_plan import build_action_plan
from .auth import _current_role, require_staff
from .directory import load_directory
from .matching import match
from .pathways import generate_pathways
from .persistence import get_store
from .safety import check_text
from .schemas import (
    ActionPlan,
    AssessmentRequest,
    MatchResult,
    Pathway,
    ResidentAssessment,
    StrictModel,
)
from .settings import get_settings

router = APIRouter(prefix="/api/bolton-connect", tags=["bolton-connect"])


# ---------------------------------------------------------------------------
# Request / response models (endpoint-specific)
# ---------------------------------------------------------------------------


class PlanRequest(AssessmentRequest):
    resident_name: str = Field(default="Resident", max_length=80)
    consent_save: bool = False
    consent_share: bool = False

    @field_validator("resident_name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        return check_text(value) or "Resident"


class PlanResponse(StrictModel):
    assessment: ResidentAssessment
    plan: ActionPlan
    session_id: str | None = None
    case_id: str | None = None
    needs_human_review: bool = True


class CaseUpdateRequest(StrictModel):
    status: Literal["new", "in_review", "actioned", "closed"] | None = None
    assigned_to: str | None = Field(default=None, max_length=80)


class CaseNoteRequest(StrictModel):
    note: str = Field(min_length=1, max_length=2000)

    @field_validator("note")
    @classmethod
    def _clean_note(cls, value: str) -> str:
        return check_text(value)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _public_service(service) -> dict:
    data = service.model_dump(mode="json")
    data["contact"] = service.public_contact()  # withheld unless verified
    data["auto_recommendable"] = service.auto_recommendable
    return data


def _case_flags(assessment: ResidentAssessment, result: MatchResult) -> list[str]:
    flags: list[str] = []
    if assessment.clarification_required:
        flags.append("clarification_required")
    if any(not r.auto_recommended for r in result.recommendations):
        flags.append("unverified_or_caveated_recommendation")
    text = " ".join(assessment.barriers).lower()
    if any(k in text for k in ("health", "disability", "lifting", "physical")):
        flags.append("health_or_disability_support")
    return flags


def _case_summary(assessment: ResidentAssessment, result: MatchResult) -> str:
    # Deliberately free of the resident's name or raw free text.
    goals = ", ".join(assessment.goals[:2]) or "no goal stated yet"
    return (
        f"Employment status: {assessment.employment_status}. Goals: {goals}. "
        f"{len(result.recommendations)} service(s) matched; human review required."
    )


# ---------------------------------------------------------------------------
# Public / resident endpoints
# ---------------------------------------------------------------------------


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    directory = load_directory(settings)
    return {
        "status": "ok",
        "module": "bolton-connect",
        "borough": settings.borough,
        "provider": settings.llm_provider,
        "demo_mode": settings.demo_mode,
        "directory_size": len(directory),
    }


@router.get("/directory")
def directory() -> dict:
    settings = get_settings()
    d = load_directory(settings)
    return {"notice": d.notice, "services": [_public_service(s) for s in d.all()]}


@router.post("/assess", response_model=ResidentAssessment)
def post_assess(payload: AssessmentRequest) -> ResidentAssessment:
    return assess(payload, get_settings())


@router.post("/match", response_model=MatchResult)
def post_match(payload: AssessmentRequest) -> MatchResult:
    settings = get_settings()
    assessment = assess(payload, settings)
    return match(assessment, payload.profile, settings)


@router.post("/pathways", response_model=list[Pathway])
def post_pathways(payload: AssessmentRequest) -> list[Pathway]:
    settings = get_settings()
    assessment = assess(payload, settings)
    return generate_pathways(assessment, settings)


@router.post("/plan", response_model=PlanResponse)
def post_plan(payload: PlanRequest) -> PlanResponse:
    settings = get_settings()
    request = AssessmentRequest(text=payload.text, profile=payload.profile)
    assessment = assess(request, settings)
    result = match(assessment, payload.profile, settings)
    pathways = generate_pathways(assessment, settings)
    plan = build_action_plan(
        assessment,
        result,
        pathways,
        payload.profile,
        resident_name=payload.resident_name,
        settings=settings,
    )

    session_id: str | None = None
    case_id: str | None = None
    if payload.consent_save or payload.consent_share:
        store = get_store(settings)
        session_id = store.save_session(
            resident_name=payload.resident_name,
            consent_save=payload.consent_save,
            consent_share=payload.consent_share,
            request=request.model_dump(mode="json"),
            result=plan.model_dump(mode="json"),
        )
        if payload.consent_share:
            case_id = store.create_case(
                session_id=session_id,
                summary=_case_summary(assessment, result),
                needs_review=True,
                flags=_case_flags(assessment, result),
            )

    return PlanResponse(
        assessment=assessment,
        plan=plan,
        session_id=session_id,
        case_id=case_id,
        needs_human_review=result.needs_human_review,
    )


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    store = get_store(get_settings())
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return session


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str) -> dict:
    store = get_store(get_settings())
    return {"deleted": store.delete_session(session_id)}


# ---------------------------------------------------------------------------
# Adviser / staff endpoints
# ---------------------------------------------------------------------------


@router.get("/cases", dependencies=[Depends(require_staff)])
def list_cases(status: str | None = None) -> dict:
    store = get_store(get_settings())
    return {"cases": store.list_cases(status)}


@router.get("/cases/{case_id}", dependencies=[Depends(require_staff)])
def get_case(case_id: str) -> dict:
    store = get_store(get_settings())
    case = store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    return case


@router.patch("/cases/{case_id}", dependencies=[Depends(require_staff)])
def update_case(case_id: str, payload: CaseUpdateRequest) -> dict:
    store = get_store(get_settings())
    ok = store.update_case(case_id, status=payload.status, assigned_to=payload.assigned_to)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found or nothing to update.")
    return store.get_case(case_id)


@router.post("/cases/{case_id}/notes")
def add_case_note(case_id: str, payload: CaseNoteRequest, role: str = Depends(require_staff)) -> dict:
    store = get_store(get_settings())
    if not store.add_case_note(case_id, role, payload.note):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    return store.get_case(case_id)


@router.get("/stats", dependencies=[Depends(require_staff)])
def stats() -> dict:
    store = get_store(get_settings())
    return store.aggregate_stats()
