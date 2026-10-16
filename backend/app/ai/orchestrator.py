import re
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers import get_provider
from app.ai.retrieval import passage, tokens
from app.ai.tools import TOOLS
from app.core.safety import safe_excerpt
from app.core.settings import Settings
from app.database.models import Case
from app.modules.base import CivicModule, Classification
from app.schemas.api import Analysis, Source, WorkflowStep
from app.services.config import ChallengeConfig


def priority_for(message: str) -> str:
    lower = message.lower()
    emergency = ["immediate danger", "life threatening", "can't breathe", "cannot breathe", "gas leak", "fire in", "suicide", "kill myself"]
    high = ["homeless", "evict", "no food", "no heating", "vulnerable", "injur", "danger", "child", "mould", "mold", "urgent", "high priority"]
    if any(term in lower for term in emergency):
        return "urgent"
    if any(term in lower for term in high):
        return "high"
    return "normal"


def potential_duplicate(db: Session, message: str, borough: str, module_id: str) -> int | None:
    if module_id != "triage":
        return None
    query = tokens(message)
    candidates = db.scalars(select(Case).where(Case.borough == borough, Case.module_id == module_id, Case.status != "resolved").order_by(Case.id.desc()).limit(200))
    best_id, best_score = None, 0.0
    for case in candidates:
        previous = tokens(case.message)
        score = len(query & previous) / max(1, len(query | previous))
        if score >= 0.74 and score > best_score:
            best_id, best_score = case.id, score
    return best_id


def analyse(message: str, borough: str, module: CivicModule, settings: Settings, config: ChallengeConfig,
            db: Session) -> tuple[Analysis, Classification, str]:
    started = perf_counter()
    classification = module.classify(message)
    priority = priority_for(message)
    retrieval = TOOLS.invoke("retrieve_approved_resources", {"message": message, "borough": borough, "module_ids": module.resource_modules}, db)
    recommendations = module.recommend(message, retrieval.resources)
    # A module can narrow usable sources (e.g. job matching excludes training records).
    recommended_titles = {item.title for item in recommendations}
    chosen = [(r, score) for r, score in retrieval.resources if r.title in recommended_titles]
    sources = [Source(resource_id=r.id, title=r.title, excerpt=passage(r, message), source_label=r.source_label,
                      source_url=r.source_url, synthetic=r.synthetic) for r, _ in chosen]
    confidence = retrieval.confidence if sources else 0.18
    duplicate = potential_duplicate(db, message, borough, module.id)
    reasons = []
    if not sources:
        reasons.append("Insufficient approved evidence for this request")
    if confidence < config.escalation_threshold:
        reasons.append("Confidence below the administrator's review threshold")
    if config.challenge.human_review_required:
        reasons.append("Challenge configuration requires human review")
    if classification.sensitive or priority in {"high", "urgent"} or module.id == "triage":
        reasons.append("Consequential advice, safety concern or routing needs staff confirmation")
    if duplicate is not None:
        reasons.append("Potential duplicate requires a staff comparison")
    needs_review = bool(reasons)
    summary = f"{classification.intent}: {safe_excerpt(message, 220)}"
    if not sources:
        summary += " No relevant approved evidence was found; staff should verify available options."
    else:
        summary += f" {len(sources)} source-backed option(s) are ready for review."
    provider = get_provider(settings).annotate(message, [source.model_dump() for source in sources], summary)
    notes = ["Guidance does not approve, reject or determine eligibility for a service.", module.explain(message)]
    if settings.demo_mode:
        notes.append("DEMO MODE: fictional data is used. These records are not official council services.")
    if any(source.synthetic for source in sources):
        notes.append("Synthetic sources illustrate the workflow; verify real availability using approved official information.")
    if not sources:
        notes.append("We cannot verify a suitable service from the available catalogue. A human must check appropriate sources.")
    if priority == "urgent":
        notes.append("This application is not monitored for emergencies. For immediate danger in the UK, contact emergency services on 999.")
    if duplicate is not None:
        notes.append("Duplicate similarity is a suggestion only; records have not been merged.")
    if provider.fallback_note:
        notes.append(provider.fallback_note)
    steps = [
        WorkflowStep(name="Input and intent", status="complete", detail=f"Validated text; category: {classification.category}."),
        WorkflowStep(name="Approved evidence retrieval", status="complete" if sources else "warning", detail=f"{len(sources)} relevant source passage(s) in {borough}; metadata preserved."),
        WorkflowStep(name="Module workflow", status="complete" if recommendations else "warning", detail=module.explain(message)),
        WorkflowStep(name="Safety and staff review", status="review" if needs_review else "complete", detail="; ".join(reasons) if reasons else "No configured review trigger; all service facts still require current verification."),
    ]
    if module.id == "triage":
        steps.insert(3, WorkflowStep(name="Potential duplicate check", status="review" if duplicate else "complete", detail=f"Compare case {duplicate} manually." if duplicate else "No close match among recent unresolved triage reports."))
    analysis = Analysis(summary=provider.summary, intent=classification.intent, confidence=confidence, needs_human_review=needs_review,
                        escalation_reason="; ".join(reasons) if reasons else None, recommendations=recommendations, sources=sources,
                        safety_notes=notes, workflow_steps=steps, provider=provider.provider, simulated=provider.simulated,
                        processing_ms=max(1, round((perf_counter() - started) * 1000)), duplicate_of=duplicate)
    return analysis, classification, priority

