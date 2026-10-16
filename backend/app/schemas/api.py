from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.core.safety import check_text
from app.core.settings import BOROUGHS

def known_module_ids():
    # Resolve the live plugin registry lazily to avoid an import cycle at startup.
    from app.modules.registry import MODULES
    return MODULES.keys()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Challenge(StrictModel):
    borough: str
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(max_length=2000)
    problem_statement: str = Field(max_length=3000)
    target_users: list[str] = Field(max_length=30)
    desired_outcomes: list[str] = Field(max_length=30)
    selected_modules: list[str] = Field(max_length=12)
    success_metrics: list[str] = Field(max_length=30)
    constraints: list[str] = Field(max_length=30)
    data_sources: list[str] = Field(max_length=30)
    demo_scenario: str = Field(max_length=3000)
    human_review_required: bool

    @field_validator("borough")
    @classmethod
    def borough_valid(cls, value):
        if value not in BOROUGHS:
            raise ValueError("Choose one of the ten Greater Manchester boroughs.")
        return value

    @field_validator("selected_modules")
    @classmethod
    def modules_valid(cls, value):
        if len(value) != len(set(value)) or any(item not in known_module_ids() for item in value):
            raise ValueError("Unknown or repeated module id.")
        return value

    @field_validator("target_users", "desired_outcomes", "success_metrics", "constraints", "data_sources")
    @classmethod
    def lists_bounded(cls, values):
        if any(not item.strip() or len(item) > 500 for item in values):
            raise ValueError("List values must be nonempty and no longer than 500 characters.")
        for item in values:
            check_text(item)
        return values

    @field_validator("title", "description", "problem_statement", "demo_scenario")
    @classmethod
    def config_text(cls, value):
        return check_text(value)


class ChallengeConfig(StrictModel):
    challenge: Challenge
    escalation_threshold: float = Field(default=0.62, ge=0, le=1)


class EnquiryInput(StrictModel):
    message: str = Field(min_length=8, max_length=3000)
    module_id: str
    borough: str | None = None
    resident_name: str = Field(default="Anonymous resident", min_length=1, max_length=100)

    @field_validator("message", "resident_name")
    @classmethod
    def safe_text(cls, value):
        return check_text(value)

    @field_validator("module_id")
    @classmethod
    def known_module(cls, value):
        if value not in known_module_ids():
            raise ValueError("Unknown module id.")
        return value

    @field_validator("borough")
    @classmethod
    def known_borough(cls, value):
        if value is not None and value not in BOROUGHS:
            raise ValueError("Unknown borough.")
        return value


class CaseUpdate(StrictModel):
    status: Literal["in_review", "resolved"]
    review_note: str = Field(min_length=8, max_length=2000)

    @field_validator("review_note")
    @classmethod
    def safe_note(cls, value):
        return check_text(value)


class DocumentInput(StrictModel):
    title: str = Field(min_length=3, max_length=180)
    content: str = Field(min_length=40, max_length=20000)
    borough: str
    module_id: str
    source_label: str = Field(min_length=3, max_length=180)
    source_url: HttpUrl | None = None
    synthetic: bool
    approved: bool

    @field_validator("title", "content", "source_label")
    @classmethod
    def safe_text(cls, value):
        return check_text(value)

    @field_validator("borough")
    @classmethod
    def borough_valid(cls, value):
        if value not in BOROUGHS:
            raise ValueError("Unknown borough.")
        return value

    @field_validator("module_id")
    @classmethod
    def module_valid(cls, value):
        if value not in known_module_ids():
            raise ValueError("Unknown module id.")
        return value


class FeedbackInput(StrictModel):
    rating: int = Field(ge=1, le=5, strict=True)


class Recommendation(BaseModel):
    title: str
    description: str
    next_steps: list[str]
    match_score: float | None = None
    skills_gap: list[str] = Field(default_factory=list)


class Source(BaseModel):
    resource_id: int
    title: str
    excerpt: str
    source_label: str
    source_url: str | None
    synthetic: bool


class WorkflowStep(BaseModel):
    name: str
    status: Literal["complete", "review", "warning"]
    detail: str


class Analysis(BaseModel):
    summary: str
    intent: str
    confidence: float = Field(ge=0, le=1)
    needs_human_review: bool
    escalation_reason: str | None
    recommendations: list[Recommendation]
    sources: list[Source]
    safety_notes: list[str]
    workflow_steps: list[WorkflowStep]
    provider: str
    simulated: bool
    processing_ms: int = Field(ge=0)
    duplicate_of: int | None

