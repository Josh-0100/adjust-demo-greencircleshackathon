from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import Field, field_validator
from sqlalchemy.orm import Session

from app.core.auth import actor_role
from app.core.safety import check_text
from app.core.settings import BOROUGHS
from app.database.session import get_db
from app.modules.base import CivicModule, Classification, EvaluationCriterion, ModuleImpactMetric
from app.schemas.api import EnquiryInput, StrictModel

router = APIRouter(prefix="/custom", tags=["custom-workflow"])


class HomeAssessmentInput(StrictModel):
    """Example challenge-specific model: replace independently of the core Case model."""
    borough: str | None = None
    resident_name: str = Field(default="Anonymous resident", min_length=1, max_length=100)
    home_type: Literal["flat", "house", "other"]
    risk_flags: list[Literal["cold", "damp", "bills"]] = Field(min_length=1, max_length=3)
    household_vulnerability: bool
    goal: str = Field(min_length=8, max_length=1000)

    @field_validator("borough")
    @classmethod
    def borough_valid(cls, value):
        if value is not None and value not in BOROUGHS:
            raise ValueError("Unknown borough.")
        return value

    @field_validator("resident_name", "goal")
    @classmethod
    def safe_text(cls, value):
        return check_text(value)

    @field_validator("risk_flags")
    @classmethod
    def unique_flags(cls, values):
        if len(values) != len(set(values)):
            raise ValueError("Repeated risk flags are not accepted.")
        return values


@router.post("/assess")
def assess_home(body: HomeAssessmentInput, request: Request, db: Session = Depends(get_db), actor: str = Depends(actor_role)):
    from app.services.cases import create_case, case_data
    flags = sorted(body.risk_flags)
    risk = "high" if body.household_vulnerability or {"cold", "damp"}.issubset(flags) else "normal"
    context = f"I live in a {body.home_type}. Concerns: {', '.join(flags)}. "
    if body.household_vulnerability:
        context += "A vulnerable person in my household needs additional support. "
    elif risk == "high":
        context += "High priority human review is requested for combined cold and damp concerns. "
    case = create_case(EnquiryInput(message=context + body.goal, module_id="custom", borough=body.borough,
                                   resident_name=body.resident_name), request.app.state.settings, db, actor)
    assessment = {"risk_level": risk, "flags": flags, "next_steps": ["Ask a trained adviser to review the home concerns.", "Confirm current approved support and referral routes before taking action."], "human_review_required": True}
    return {"assessment": assessment, "case": case_data(case)}


class CustomChallenge(CivicModule):
    id = "custom"
    name = "Custom Challenge · Warm Homes"
    description = "An implemented adaptable assessment workflow for cold homes, damp and bills."
    icon = "Sparkles"
    input_hint = "Describe your home concerns and the outcome you need."
    example_prompt = "My flat has damp and is hard to keep warm. I need a safe plan and a human adviser."
    capabilities = ["Custom structured assessment", "Risk flags", "Grounded referral suggestions", "Human review", "Extensible APIs"]
    workflow_steps = ["Assess structured concerns", "Retrieve approved evidence", "Prepare safe next steps", "Queue human review"]
    resource_modules = ["custom", "service-navigator"]
    router = router

    def classify(self, message):
        return Classification("Warm homes assessment", "Housing and Energy Review", "Prepare a home-support assessment", True)

    def explain(self, message):
        return "This example applies an explicit home-concerns checklist. It does not assess legal eligibility, diagnose health conditions or approve financial support."

    def evaluate(self, message, analysis):
        source_titles = {source.title for source in analysis.sources}
        return [
            EvaluationCriterion(key="warm_home_human_review", passed=analysis.needs_human_review,
                                detail="Custom home-support workflow must always require human review."),
            EvaluationCriterion(key="warm_home_grounding", passed=all(item.title in source_titles for item in analysis.recommendations),
                                detail="Every suggested resource must occur in the retrieved source list."),
        ]

    def impact_metrics(self, cases, evaluations):
        own_cases = {case.id for case in cases if case.module_id == self.id}
        own_evaluations = [row for row in evaluations if row.case_id in own_cases]
        checks = [check for row in own_evaluations for check in row.criteria]
        return [ModuleImpactMetric(key="custom_assessments", label="Custom workflow assessments", value=len(own_cases), unit="cases", kind="observed",
                                   description="Recorded warm-home workflow cases. Demo cases are fictional; this is not a council outcome study."),
                ModuleImpactMetric(key="custom_safeguard_checks", label="Warm-home safeguards checked", value=sum(check["passed"] for check in checks), unit="checks", kind="prototype_test",
                                   description=f"Passed {sum(check['passed'] for check in checks)} of {len(checks)} runtime review and source-grounding checks. These checks do not measure recommendation accuracy or real-world effectiveness.")]

