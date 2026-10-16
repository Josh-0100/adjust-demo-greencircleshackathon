from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Answers(StrictModel):
    role: str = Field(default="", max_length=120)
    tasks: str = Field(default="", max_length=500)
    barriers: str = Field(default="", max_length=500)
    constraints: str = Field(default="", max_length=500)
    employee_view: str = Field(default="", max_length=500)


class AnalyseRequest(StrictModel):
    description: str = Field(min_length=20, max_length=4000)
    role: str = Field(default="", max_length=120)
    constraints: str = Field(default="", max_length=500)
    answers: Answers = Field(default_factory=Answers)
    use_ai: bool = False


class Analysis(StrictModel):
    role: str | None = None
    tasks: list[str] = Field(default_factory=list)
    barriers: list[str] = Field(default_factory=list)
    reported_limitations: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    clarification_required: bool = False
    scenarios: list[str] = Field(default_factory=list)


class Question(StrictModel):
    id: Literal["role", "tasks", "barriers", "constraints", "employee_view"]
    question: str
    hint: str
    required: bool = False


class KnowledgeEntry(StrictModel):
    id: str
    topic: str
    summary: str
    official_url: str
    publisher: str
    last_reviewed: date
    content_owner: str
    scenarios: list[str]
    verification_status: Literal["verified", "pending", "withdrawn"]
    evidence_locator: str
    review_due: date


class Recommendation(StrictModel):
    id: str
    title: str
    barrier_addressed: str
    steps: list[str]
    employee_questions: list[str]
    source_ids: list[str]
    limitations: str
    referral_guidance: str
    effort: Literal["Start with a conversation", "Review the task", "Explore equipment"]


class Conversation(StrictModel):
    opening: str
    questions: list[str]
    potential_options: list[str]
    agreement_summary: str
    follow_up: list[str]
    source_ids: list[str]


class Referral(StrictModel):
    id: str
    name: str
    publisher: str
    provides: str
    eligibility: str
    access: str
    official_url: str
    verified_on: date
    status: Literal["guidance_checked", "confirm_availability"]
    limitations: str


class Safety(StrictModel):
    level: Literal["routine", "urgent", "emergency"] = "routine"
    title: str = "Options to discuss, with human review"
    message: str = "ADJUST does not diagnose, determine disability or fitness for work, or make employment decisions."
    actions: list[str] = Field(default_factory=list)
    official_url: str | None = None


class AnalyseResponse(StrictModel):
    status: Literal["ready", "clarification", "insufficient_evidence", "urgent", "emergency"]
    analysis: Analysis
    questions: list[Question]
    recommendations: list[Recommendation]
    conversation: Conversation | None
    sources: list[KnowledgeEntry]
    referrals: list[Referral]
    safety: Safety
    provider: str
    simulated: bool
    provider_note: str | None = None
    human_review_required: Literal[True] = True
    data_persisted: Literal[False] = False
    notices: list[str]
    created_on: date


class PlanRequest(StrictModel):
    situation: AnalyseRequest
    selected_ids: list[str] = Field(min_length=1, max_length=3)
    next_steps: str = Field(min_length=5, max_length=500)
    review_date: date
    human_reviewed: bool

    @field_validator("selected_ids")
    @classmethod
    def unique_selection(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("Choose each adjustment once.")
        return value


class Plan(StrictModel):
    title: str
    status: Literal["Discussion draft"] = "Discussion draft"
    workplace_situation: str
    barriers: list[str]
    adjustments: list[Recommendation]
    discussion_questions: list[str]
    agreed_next_steps: str
    external_support: list[Referral]
    review_date: date
    sources: list[KnowledgeEntry]
    disclaimer: str
    created_on: date
    human_reviewed: Literal[True] = True
