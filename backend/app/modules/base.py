from dataclasses import dataclass
import re

from app.database.models import Resource
from app.schemas.api import Analysis, Recommendation
from pydantic import BaseModel
from typing import Literal


class EvaluationCriterion(BaseModel):
    key: str
    passed: bool
    detail: str


class ModuleImpactMetric(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    kind: Literal["observed", "prototype_test", "estimated", "simulated"]
    description: str

SKILL_ALIASES = {
    "communication": ["communication", "customer service", "customer support", "speaking with people", "retail"],
    "teamwork": ["teamwork", "team work", "team player", "retail"],
    "digital literacy": ["digital literacy", "computer skills", "using computers", "email", "digital skills"],
    "spreadsheets": ["spreadsheets", "spreadsheet", "excel"],
    "care": ["care experience", "carer", "care worker", "caring for"],
    "practical skills": ["practical skills", "diy", "construction", "building experience", "repair experience"],
    "health and safety": ["health and safety", "safety training", "cscs"],
    "gardening": ["gardening", "growing vegetables", "garden experience"],
}


def extract_skills(message: str) -> list[str]:
    lower = message.lower()
    found = []
    for skill, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            for match in re.finditer(r"\b" + re.escape(alias) + r"\b", lower):
                prefix = lower[max(0, match.start() - 45):match.start()]
                if re.search(r"(?:no|not|lack|without|learn|learning|need|want to)\b[^.!?]{0,30}$", prefix):
                    continue
                found.append(skill)
                break
            if skill in found:
                break
    return sorted(found)


@dataclass
class Classification:
    category: str
    department: str
    intent: str
    sensitive: bool = False


class CivicModule:
    """Small plugin interface. Register a subclass in registry.py; core routing stays unchanged.

    descriptor supplies UI metadata. resource_modules maps approved catalogues.
    classify provides deterministic categorisation. recommend only receives retrieved sources.
    router is an optional FastAPI APIRouter for specialised input/persistence.
    """

    id: str
    name: str
    description: str
    icon: str
    input_hint: str
    example_prompt: str
    capabilities: list[str]
    workflow_steps: list[str]
    resource_modules: list[str]
    router = None

    def descriptor(self, enabled: bool):
        return {key: getattr(self, key) for key in ["id", "name", "description", "icon", "input_hint", "example_prompt", "capabilities", "workflow_steps"]} | {"enabled": enabled}

    def classify(self, message: str) -> Classification:
        raise NotImplementedError

    def recommend(self, message: str, resources: list[tuple[Resource, float]]) -> list[Recommendation]:
        return [Recommendation(title=resource.title, description=resource.description,
                               next_steps=resource.next_steps, match_score=None, skills_gap=[])
                for resource, _ in resources[:3]]

    def explain(self, message: str) -> str:
        return "Recommendations are based only on the approved retrieved catalogue."

    def evaluate(self, message: str, analysis: Analysis) -> list[EvaluationCriterion]:
        """Optional module-specific runtime safeguards; never substitute for accuracy benchmarks."""
        return []

    def impact_metrics(self, cases: list, evaluations: list) -> list[ModuleImpactMetric]:
        """Optional module-specific aggregate metrics with explicit evidence kinds."""
        return []


def category_match(message: str, categories: list[tuple[list[str], Classification]], fallback: Classification):
    lower = message.lower()
    ranked = [(sum(1 for word in words if word in lower), result) for words, result in categories]
    best = max(ranked, key=lambda row: row[0], default=(0, fallback))
    return best[1] if best[0] else fallback

