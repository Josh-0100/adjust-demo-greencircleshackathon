"""Typed contracts for Bolton Connect.

These Pydantic models are the single source of truth for the resident
assessment, the support directory, matching results, pathways and the action
plan. They are deliberately strict and bounded: no field ever encodes a medical
diagnosis, a fitness-for-work judgement, or an entitlement decision.
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .safety import check_text

# ---------------------------------------------------------------------------
# Enumerations and labels
# ---------------------------------------------------------------------------

EmploymentStatus = Literal[
    "unemployed",
    "employed",
    "self_employed",
    "economically_inactive",
    "student",
    "retired",
    "unknown",
]

# Phase 5 eligibility states. Lowercase on the wire; UI maps to the uppercase
# labels in the brief.
EligibilityState = Literal["eligible", "potentially_eligible", "not_eligible", "unknown"]

ELIGIBILITY_LABELS: dict[str, str] = {
    "eligible": "ELIGIBLE",
    "potentially_eligible": "POTENTIALLY ELIGIBLE",
    "not_eligible": "NOT ELIGIBLE",
    "unknown": "UNKNOWN",
}

# Phase 4 support categories.
SupportCategory = Literal[
    "employment_assistance",
    "skills_training",
    "disability_employment_support",
    "financial_guidance",
    "wellbeing_support",
    "workplace_adjustments",
    "community_support",
    "digital_inclusion",
]

VerificationStatus = Literal["verified", "source_listed", "unverified", "expired", "historical"]

# Where a piece of information came from — drives the "verified vs AI-suggested"
# distinction required for the action plan.
Provenance = Literal[
    "verified",
    "official_source",
    "ai_suggestion",
    "resident_stated",
    "synthetic_demo",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# ---------------------------------------------------------------------------
# Phase 2/3 — resident input and structured assessment
# ---------------------------------------------------------------------------


class ResidentProfile(StrictModel):
    """Optional, resident-stated structured fields that sharpen deterministic
    eligibility checks. Every field is self-declared and optional. Health or
    disability is a practical, self-reported support need — never a diagnosis."""

    borough: str | None = "Bolton"
    age_band: Literal["16-17", "18-24", "25-49", "50-64", "65+", "prefer_not_to_say"] | None = None
    employment_status: EmploymentStatus | None = None
    unemployed_duration: Literal["under_6_months", "6_to_12_months", "1_to_2_years", "over_2_years", "unknown"] | None = None
    has_health_condition_or_disability: bool | None = None
    digital_confidence: Literal["low", "medium", "high"] | None = None
    receives_benefits: bool | None = None

    @field_validator("borough")
    @classmethod
    def _clean_borough(cls, value: str | None) -> str | None:
        return check_text(value) if value else value


class AssessmentRequest(StrictModel):
    """A resident describes their circumstances in plain English."""

    text: str = Field(min_length=10, max_length=4000)
    profile: ResidentProfile = Field(default_factory=ResidentProfile)

    @field_validator("text")
    @classmethod
    def _safe_text(cls, value: str) -> str:
        return check_text(value)


class ResidentAssessment(StrictModel):
    """Structured extraction of a resident's situation (Phase 3).

    Matches the brief's schema and adds provenance/safety fields. ``barriers``
    are practical limitations stated by the resident (e.g. "difficulty with
    heavy lifting"), never clinical findings.
    """

    employment_status: EmploymentStatus = "unknown"
    experience: list[str] = Field(default_factory=list, max_length=40)
    skills: list[str] = Field(default_factory=list, max_length=40)
    goals: list[str] = Field(default_factory=list, max_length=20)
    barriers: list[str] = Field(default_factory=list, max_length=20)
    support_needs: list[str] = Field(default_factory=list, max_length=20)
    training_interests: list[str] = Field(default_factory=list, max_length=20)
    support_preferences: list[str] = Field(default_factory=list, max_length=20)
    clarification_required: bool = False
    clarifying_question: str | None = Field(default=None, max_length=300)

    # Transparency fields — not part of the brief's minimal example but required
    # for honest UI. confidence is an uncalibrated coverage signal, not accuracy.
    confidence: float = Field(default=0.0, ge=0, le=1)
    provider: str = "deterministic"
    disclaimers: list[str] = Field(default_factory=list, max_length=12)


# ---------------------------------------------------------------------------
# Phase 4 — support directory
# ---------------------------------------------------------------------------


class EligibilityCondition(StrictModel):
    """A single published eligibility criterion.

    ``label`` is the plain-English criterion shown to residents and advisers.
    ``kind``/``params`` let the deterministic engine evaluate the condition
    against a resident profile where possible; anything it cannot evaluate from
    available information becomes "missing information", never a silent pass.
    """

    id: str = Field(min_length=1, max_length=60)
    label: str = Field(min_length=1, max_length=300)
    kind: Literal[
        "geographic",
        "employment_status",
        "age",
        "health_or_disability",
        "referral_required",
        "residency",
        "benefit_status",
        "other",
    ]
    params: dict = Field(default_factory=dict)


class SupportService(StrictModel):
    """One record in the Bolton support directory (Phase 4)."""

    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1200)
    provider: str = Field(min_length=1, max_length=200)
    borough: str = Field(min_length=1, max_length=60)
    category: SupportCategory

    eligibility: list[EligibilityCondition] = Field(default_factory=list, max_length=20)
    referral_requirements: list[str] = Field(default_factory=list, max_length=12)

    source_label: str = Field(min_length=1, max_length=200)
    source_url: str | None = None
    last_verified: date | None = None
    verification_status: VerificationStatus = "unverified"
    content_owner: str = Field(min_length=1, max_length=120)
    contact: str | None = Field(default=None, max_length=300)

    # Time-limited programmes (e.g. Working Well / WorkWell) default to needing
    # verification before they can be recommended automatically.
    active: bool = True
    synthetic: bool = True
    notes: list[str] = Field(default_factory=list, max_length=12)

    @property
    def auto_recommendable(self) -> bool:
        """A service may be recommended automatically only if it is active and
        its details are verified or taken from an attributed official source.
        Unverified, expired or historical programmes are surfaced only with an
        explicit "confirm availability" caveat (Phase 4 rule)."""
        return self.active and self.verification_status in {"verified", "source_listed"}

    def public_contact(self) -> str | None:
        # Never expose contact details for anything not operationally verified.
        return self.contact if self.verification_status == "verified" else None


# ---------------------------------------------------------------------------
# Phase 5 — matching results
# ---------------------------------------------------------------------------


class SourceRef(StrictModel):
    label: str
    url: str | None = None
    last_verified: date | None = None
    verification_status: VerificationStatus = "unverified"
    synthetic: bool = True


class SupportRecommendation(StrictModel):
    service_id: str
    name: str
    provider: str
    category: SupportCategory
    eligibility_state: EligibilityState
    eligibility_label: str = ""
    why_it_helps: str = Field(max_length=600)
    reasons: list[str] = Field(default_factory=list, max_length=20)
    missing_information: list[str] = Field(default_factory=list, max_length=20)
    next_steps: list[str] = Field(default_factory=list, max_length=12)
    caveats: list[str] = Field(default_factory=list, max_length=12)
    auto_recommended: bool = False
    source: SourceRef

    @field_validator("eligibility_label", mode="before")
    @classmethod
    def _fill_label(cls, value, info):
        state = info.data.get("eligibility_state")
        return value or ELIGIBILITY_LABELS.get(state, "")


class MatchResult(StrictModel):
    assessment: ResidentAssessment
    recommendations: list[SupportRecommendation] = Field(default_factory=list)
    needs_human_review: bool = True
    review_reasons: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    provider: str = "deterministic"
    processing_ms: int = Field(default=0, ge=0)


# ---------------------------------------------------------------------------
# Phase 6 — employment & training pathways
# ---------------------------------------------------------------------------


class TrainingStep(StrictModel):
    title: str
    provider: str
    builds_skills: list[str] = Field(default_factory=list, max_length=12)
    source: SourceRef
    note: str | None = Field(default=None, max_length=300)


class Opportunity(StrictModel):
    title: str
    sector: str
    status: Literal["demonstration", "verified_vacancy"] = "demonstration"
    employer: str | None = None
    source: SourceRef
    # Always present for demonstration items so mock roles are never shown as live.
    disclaimer: str = "Demonstration opportunity — not a live vacancy."


class Pathway(StrictModel):
    interest: str
    target_sector: str
    current_skills: list[str] = Field(default_factory=list, max_length=40)
    skill_gaps: list[str] = Field(default_factory=list, max_length=40)
    training: list[TrainingStep] = Field(default_factory=list, max_length=12)
    opportunities: list[Opportunity] = Field(default_factory=list, max_length=12)
    next_actions: list[str] = Field(default_factory=list, max_length=12)
    caveats: list[str] = Field(default_factory=list, max_length=12)


# ---------------------------------------------------------------------------
# Phase 7 — personalised action plan
# ---------------------------------------------------------------------------


class PlanItem(StrictModel):
    """A single line in the action plan, tagged with where it came from so the
    UI can clearly separate verified facts from AI-generated suggestions."""

    text: str = Field(min_length=1, max_length=600)
    provenance: Provenance = "ai_suggestion"
    source_label: str | None = None
    source_url: str | None = None
    last_verified: date | None = None


class ActionPlan(StrictModel):
    resident_name: str = "Resident"
    borough: str = "Bolton"
    generated_at: str = ""
    provider: str = "deterministic"

    # 1–10 as specified in Phase 7.
    goals: list[PlanItem] = Field(default_factory=list)
    strengths: list[PlanItem] = Field(default_factory=list)
    barriers: list[PlanItem] = Field(default_factory=list)
    recommended_services: list[SupportRecommendation] = Field(default_factory=list)
    training_opportunities: list[PlanItem] = Field(default_factory=list)
    employment_exploration: list[Pathway] = Field(default_factory=list)
    immediate_next_steps: list[PlanItem] = Field(default_factory=list)
    longer_term_milestones: list[PlanItem] = Field(default_factory=list)
    human_support_contacts: list[PlanItem] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)

    disclaimer: str = (
        "This plan is a prototype. Verified facts are labelled; all other items "
        "are AI-generated suggestions for discussion with a human adviser. It "
        "does not assess medical fitness or confirm entitlement to any service."
    )
