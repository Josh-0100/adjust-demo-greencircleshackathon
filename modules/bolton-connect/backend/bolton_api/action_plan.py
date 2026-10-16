"""Personalised action plan (Phase 7).

Assembles the resident's assessment, matches and pathways into a single ten-part
plan. Every line is tagged with its provenance so the UI can clearly separate
what the resident told us and verified facts from AI-generated suggestions. The
plan never asserts entitlement or medical fitness.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .directory import Directory, load_directory
from .pathways import generate_pathways
from .schemas import (
    ActionPlan,
    MatchResult,
    Pathway,
    PlanItem,
    Provenance,
    ResidentAssessment,
    ResidentProfile,
    SourceRef,
)
from .settings import Settings, get_settings

_STATUS_TO_PROVENANCE: dict[str, Provenance] = {
    "verified": "verified",
    "source_listed": "official_source",
    "official_source": "official_source",
    "unverified": "ai_suggestion",
    "expired": "ai_suggestion",
    "historical": "ai_suggestion",
}


def _provenance_for(source: SourceRef) -> Provenance:
    if source.synthetic:
        return "synthetic_demo"
    return _STATUS_TO_PROVENANCE.get(source.verification_status, "ai_suggestion")


def _goals(assessment: ResidentAssessment) -> list[PlanItem]:
    items = [PlanItem(text=g, provenance="resident_stated") for g in assessment.goals]
    if not items:
        items.append(
            PlanItem(
                text="Agree a clear work or training goal with your adviser.",
                provenance="ai_suggestion",
            )
        )
    return items[:10]


def _strengths(assessment: ResidentAssessment, pathways: list[Pathway]) -> list[PlanItem]:
    items = [PlanItem(text=s, provenance="resident_stated") for s in assessment.skills]
    seen = {s.text.lower() for s in items}
    # Transferable strengths inferred by the pathway generator are suggestions.
    for pathway in pathways:
        for skill in pathway.current_skills:
            if skill.lower() not in seen:
                items.append(PlanItem(text=skill, provenance="ai_suggestion"))
                seen.add(skill.lower())
    if not items:
        items.append(
            PlanItem(text="Identify your strengths together with an adviser.", provenance="ai_suggestion")
        )
    return items[:10]


def _barriers(assessment: ResidentAssessment) -> list[PlanItem]:
    return [PlanItem(text=b, provenance="resident_stated") for b in assessment.barriers][:10]


def _training_items(pathways: list[Pathway]) -> list[PlanItem]:
    items: list[PlanItem] = []
    seen: set[str] = set()
    for pathway in pathways:
        for step in pathway.training:
            key = step.title.lower()
            if key in seen:
                continue
            seen.add(key)
            items.append(
                PlanItem(
                    text=f"{step.title} (via {step.provider})",
                    provenance=_provenance_for(step.source),
                    source_label=step.source.label,
                    source_url=step.source.url,
                    last_verified=step.source.last_verified,
                )
            )
    return items[:10]


def _immediate_steps(match_result: MatchResult, assessment: ResidentAssessment) -> list[PlanItem]:
    items: list[PlanItem] = []
    if assessment.support_needs:
        items.append(
            PlanItem(
                text="Bring your stated support needs to a first adviser appointment: "
                + ", ".join(assessment.support_needs[:4])
                + ".",
                provenance="ai_suggestion",
            )
        )
    for rec in match_result.recommendations:
        if rec.auto_recommended and rec.eligibility_state == "eligible":
            items.append(
                PlanItem(
                    text=f"Get in touch with {rec.name} to talk through how they can help.",
                    provenance="official_source" if not rec.source.synthetic else "synthetic_demo",
                    source_label=rec.source.label,
                    source_url=rec.source.url,
                    last_verified=rec.source.last_verified,
                )
            )
    if not items:
        items.append(
            PlanItem(text="Book a first appointment with a Bolton employment adviser.", provenance="ai_suggestion")
        )
    return items[:10]


def _longer_term(assessment: ResidentAssessment, pathways: list[Pathway]) -> list[PlanItem]:
    items: list[PlanItem] = []
    for pathway in pathways:
        if pathway.skill_gaps:
            items.append(
                PlanItem(
                    text=f"Work towards {pathway.target_sector} roles by building: "
                    + ", ".join(pathway.skill_gaps[:4])
                    + ".",
                    provenance="ai_suggestion",
                )
            )
    items.append(
        PlanItem(text="Review progress with your adviser and adjust this plan as things change.", provenance="ai_suggestion")
    )
    return items[:10]


def _human_contacts(match_result: MatchResult, directory: Directory) -> list[PlanItem]:
    items: list[PlanItem] = []
    hub = directory.get("bolton-employment-hub")
    if hub and hub.public_contact():
        items.append(
            PlanItem(
                text=f"{hub.name}: {hub.public_contact()}",
                provenance="verified",
                source_label=hub.source_label,
                source_url=hub.source_url,
                last_verified=hub.last_verified,
            )
        )
    items.append(
        PlanItem(
            text="Ask to speak to a human adviser before acting on any AI-generated suggestion in this plan.",
            provenance="ai_suggestion",
        )
    )
    return items[:10]


def _sources(match_result: MatchResult, pathways: list[Pathway]) -> list[SourceRef]:
    sources: list[SourceRef] = []
    seen: set[tuple[str, str | None]] = set()

    def add(src: SourceRef) -> None:
        key = (src.label, src.url)
        if key not in seen:
            seen.add(key)
            sources.append(src)

    for rec in match_result.recommendations:
        add(rec.source)
    for pathway in pathways:
        for step in pathway.training:
            add(step.source)
    return sources


def build_action_plan(
    assessment: ResidentAssessment,
    match_result: MatchResult,
    pathways: list[Pathway] | None = None,
    profile: ResidentProfile | None = None,
    resident_name: str = "Resident",
    settings: Settings | None = None,
    directory: Directory | None = None,
) -> ActionPlan:
    """Assemble the ten-section action plan."""
    settings = settings or get_settings()
    directory = directory or load_directory(settings)
    profile = profile or ResidentProfile()
    if pathways is None:
        pathways = generate_pathways(assessment, settings, directory)

    return ActionPlan(
        resident_name=resident_name,
        borough=profile.borough or settings.borough,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        provider=assessment.provider,
        goals=_goals(assessment),
        strengths=_strengths(assessment, pathways),
        barriers=_barriers(assessment),
        recommended_services=match_result.recommendations,
        training_opportunities=_training_items(pathways),
        employment_exploration=pathways,
        immediate_next_steps=_immediate_steps(match_result, assessment),
        longer_term_milestones=_longer_term(assessment, pathways),
        human_support_contacts=_human_contacts(match_result, directory),
        sources=_sources(match_result, pathways),
    )
