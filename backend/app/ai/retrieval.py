from dataclasses import dataclass
import math
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Resource

STOPWORDS = set("a an the and or i my me we our am is are was were to of in on for with at as it this that there can could would should how where what which do does have has had need want please find help from by be but not about into only synthetic demonstration fictional example support pathway guidance adviser human approved real council current review confirm no must information record".split())
NORMALISE = {"bills":"bill", "skills":"skill", "spreadsheets":"spreadsheet", "cyclists":"cycle", "cycling":"cycle", "homes":"home", "roads":"road", "opportunities":"opportunity", "courses":"course", "learning":"learn", "training":"train", "volunteering":"volunteer", "volunteers":"volunteer", "gardening":"garden", "warm":"cold", "warmth":"cold", "energy":"energy", "digital":"digital", "office":"office"}


def tokens(text: str) -> set[str]:
    return {NORMALISE.get(word, word) for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 2 and word not in STOPWORDS}


@dataclass
class RetrievalResult:
    resources: list[tuple[Resource, float]]
    confidence: float


def retrieve(db: Session, message: str, borough: str, module_ids: list[str], limit: int = 3) -> RetrievalResult:
    resources = list(db.scalars(select(Resource).where(Resource.approved.is_(True), Resource.borough == borough,
                                                        Resource.module_id.in_(module_ids)).order_by(Resource.id)))
    query = tokens(message)
    if not resources or not query:
        return RetrievalResult([], 0.12)
    vocabularies = [tokens(resource.title + " " + resource.description + " " + resource.content + " " + " ".join(resource.skills)) for resource in resources]
    document_frequency = {term: sum(term in words for words in vocabularies) for term in query}
    weights = {term: math.log((len(resources) + 1) / (count + 1)) + 1 for term, count in document_frequency.items()}
    total_weight = sum(weights.values())
    ranked = []
    for resource, words in zip(resources, vocabularies):
        overlap = query & words
        coverage = sum(weights[term] for term in overlap) / total_weight
        title_overlap = len(query & tokens(resource.title + " " + resource.description)) / len(query)
        score = min(1.0, coverage * 0.8 + title_overlap * 0.2)
        if score >= 0.12 and overlap:
            ranked.append((resource, round(score, 4)))
    ranked.sort(key=lambda item: (-item[1], item[0].id))
    # A single shared word must not fill the remaining cards with weak matches.
    cutoff = max(0.16, ranked[0][1] * 0.4) if ranked else 1.0
    selected = [item for item in ranked if item[1] >= cutoff][:limit]
    confidence = round(min(0.93, 0.42 + selected[0][1] * 0.52), 2) if selected else 0.18
    return RetrievalResult(selected, confidence)


def passage(resource: Resource, message: str, limit: int = 360) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", resource.content)
    query = tokens(message)
    useful = sorted(enumerate(sentences), key=lambda row: (-len(tokens(row[1]) & query), row[0]))
    selected = [row[1] for row in useful[:2]]
    text = " ".join(selected)
    return text[:limit]

