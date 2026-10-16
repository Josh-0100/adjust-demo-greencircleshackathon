"""Employment & training pathways (Phase 6).

Given a resident's assessment, suggest one or two realistic routes towards work:
the transferable skills they already have, likely skill gaps, training that could
close them, and example opportunities. Opportunities are always clearly marked as
demonstrations — never live vacancies — unless sourced from a verified feed, and
this module has none, so every opportunity carries the demonstration disclaimer.

A health condition or disability is never a reason to exclude a route; adjustments
and support are surfaced instead.
"""
from __future__ import annotations

from .directory import Directory, load_directory
from .schemas import (
    Opportunity,
    Pathway,
    ResidentAssessment,
    SourceRef,
    TrainingStep,
)
from .settings import Settings, get_settings

# Transferable skills a resident is likely to carry out of a past sector. This
# inference lives here (not in assessment) so the assessment stays strictly to
# what the resident actually said.
_TRANSFERABLE: dict[str, list[str]] = {
    "warehouse": ["teamwork", "reliability", "working to targets", "health & safety awareness"],
    "retail": ["customer service", "handling transactions", "communication", "teamwork"],
    "hospitality": ["customer service", "working under pressure", "teamwork"],
    "catering": ["food hygiene awareness", "working under pressure", "teamwork"],
    "care": ["communication", "empathy", "reliability", "safeguarding awareness"],
    "cleaning": ["reliability", "attention to detail", "working independently"],
    "construction": ["manual skills", "health & safety awareness", "teamwork"],
    "driving": ["driving licence", "time management", "working independently"],
    "manufacturing": ["working to targets", "health & safety awareness", "teamwork"],
    "administration": ["organisation", "IT skills", "written communication"],
    "customer service": ["communication", "problem solving", "patience"],
    "security": ["vigilance", "communication", "record keeping"],
    "teaching": ["communication", "organisation", "patience"],
    "nursing": ["communication", "empathy", "record keeping"],
    "hairdressing": ["customer service", "attention to detail", "creativity"],
    "mechanic": ["problem solving", "manual skills", "attention to detail"],
    "gardening": ["working outdoors", "reliability", "physical stamina"],
    "it": ["problem solving", "IT skills", "attention to detail"],
    "finance": ["numeracy", "attention to detail", "IT skills"],
    "sales": ["communication", "persuasion", "resilience"],
}

# Target sectors a resident may move towards. "source" ids point at real
# directory services where training can genuinely be explored.
_SECTOR_PROFILE: dict[str, dict] = {
    "warehouse": {
        "typical": ["manual handling", "working to targets", "teamwork", "basic IT for scanning"],
        "training": [("Forklift / manual handling certificate", None, ["forklift", "manual handling"])],
        "roles": ["Warehouse Operative", "Pick & Pack Operative"],
    },
    "driving": {
        "typical": ["full driving licence", "route planning", "customer service", "time management"],
        "training": [("HGV / LGV licence and Driver CPC", None, ["driving licence", "professional driving"])],
        "roles": ["Delivery Driver", "Multi-drop Driver"],
    },
    "care": {
        "typical": ["communication", "empathy", "Care Certificate", "safeguarding"],
        "training": [("Care Certificate / Health & Social Care course", "bolton-college-adult-skills", ["care certificate", "safeguarding"])],
        "roles": ["Care Assistant", "Support Worker"],
    },
    "construction": {
        "typical": ["CSCS card", "manual skills", "health & safety", "teamwork"],
        "training": [("CSCS card preparation", None, ["health & safety", "site readiness"])],
        "roles": ["Labourer", "Trades Assistant"],
    },
    "customer service": {
        "typical": ["communication", "IT skills", "problem solving", "patience"],
        "training": [("Customer service skills course", "bolton-college-adult-skills", ["customer service", "communication"])],
        "roles": ["Customer Service Advisor", "Contact Centre Agent"],
    },
    "digital": {
        "typical": ["basic IT", "using online services", "email & documents", "online safety"],
        "training": [
            ("Free online digital skills", "learn-my-way", ["basic IT", "online safety"]),
            ("Digital skills course", "bolton-college-adult-skills", ["IT skills"]),
        ],
        "roles": ["Admin Assistant", "Data Entry Clerk"],
    },
    "retail": {
        "typical": ["customer service", "handling payments", "stock handling", "teamwork"],
        "training": [("Retail skills course", "bolton-college-adult-skills", ["customer service", "retail operations"])],
        "roles": ["Sales Assistant", "Customer Assistant"],
    },
    "catering": {
        "typical": ["food hygiene", "working under pressure", "teamwork"],
        "training": [("Food hygiene certificate", None, ["food hygiene"])],
        "roles": ["Kitchen Assistant", "Catering Assistant"],
    },
    "administration": {
        "typical": ["IT skills", "organisation", "written communication", "data entry"],
        "training": [("Administration / IT skills course", "bolton-college-adult-skills", ["IT skills", "organisation"])],
        "roles": ["Administrator", "Receptionist"],
    },
    "employability": {
        "typical": ["CV writing", "interview skills", "job searching", "confidence"],
        "training": [("Careers guidance and CV support", "national-careers-service", ["CV writing", "interview skills"])],
        "roles": ["Varies — explore options with an adviser"],
    },
}

_INTEREST_TO_SECTOR: dict[str, str] = {
    "Digital skills": "digital",
    "Forklift / warehouse certificate": "warehouse",
    "Driving / HGV licence": "driving",
    "Construction (CSCS)": "construction",
    "Care certificate": "care",
    "Customer service training": "customer service",
    "English or maths (functional skills)": "employability",
    "First aid certificate": "care",
    "Food hygiene certificate": "catering",
}


def _demo_source() -> SourceRef:
    return SourceRef(
        label="Adjust AI demonstration pathway data",
        url=None,
        last_verified=None,
        verification_status="unverified",
        synthetic=True,
    )


def _source_from_service(directory: Directory, service_id: str | None) -> SourceRef:
    if service_id:
        service = directory.get(service_id)
        if service:
            return SourceRef(
                label=service.source_label,
                url=service.source_url,
                last_verified=service.last_verified,
                verification_status=service.verification_status,
                synthetic=service.synthetic,
            )
    return _demo_source()


def _current_skills(assessment: ResidentAssessment) -> list[str]:
    skills = list(assessment.skills)
    for sector in assessment.experience:
        for skill in _TRANSFERABLE.get(sector, []):
            if skill not in skills:
                skills.append(skill)
    return skills[:40]


def _choose_targets(assessment: ResidentAssessment) -> list[str]:
    targets: list[str] = []
    for interest in assessment.training_interests:
        sector = _INTEREST_TO_SECTOR.get(interest)
        if sector and sector not in targets:
            targets.append(sector)
    # Progression within an existing sector if nothing else was stated.
    for sector in assessment.experience:
        if sector in _SECTOR_PROFILE and sector not in targets:
            targets.append(sector)
    if not targets:
        targets.append("employability")
    return targets[:2]


def _build_pathway(sector: str, current: list[str], directory: Directory) -> Pathway:
    profile = _SECTOR_PROFILE.get(sector, _SECTOR_PROFILE["employability"])
    current_lower = {s.lower() for s in current}
    gaps = [s for s in profile["typical"] if s.lower() not in current_lower]

    training = [
        TrainingStep(
            title=title,
            provider=(directory.get(sid).provider if sid and directory.get(sid) else "To be confirmed with a local provider"),
            builds_skills=builds,
            source=_source_from_service(directory, sid),
            note="Availability and any funding change over time — confirm with the provider." if sid else "Demonstration training step — confirm a real local course with an adviser.",
        )
        for (title, sid, builds) in profile["training"]
    ]

    opportunities = [
        Opportunity(
            title=f"{role} (example role)",
            sector=sector,
            status="demonstration",
            employer=None,
            source=_demo_source(),
        )
        for role in profile["roles"][:2]
    ]

    next_actions = [
        "Talk to Bolton Employment Hub about roles and training in this area.",
        "Use the National Careers Service to check what this kind of work involves.",
        "Ask an adviser which training is funded for your circumstances.",
    ]
    caveats = [
        "Opportunities shown are demonstrations, not live vacancies.",
        "A health condition or disability is not a barrier to exploring these routes — adjustments and support can be arranged.",
        "Training availability and funding change — confirm with the provider before enrolling.",
    ]

    return Pathway(
        interest=sector,
        target_sector=sector,
        current_skills=current,
        skill_gaps=gaps,
        training=training,
        opportunities=opportunities,
        next_actions=next_actions,
        caveats=caveats,
    )


def generate_pathways(
    assessment: ResidentAssessment,
    settings: Settings | None = None,
    directory: Directory | None = None,
) -> list[Pathway]:
    """Produce up to two employment/training pathways for a resident."""
    if assessment.clarification_required:
        return []
    settings = settings or get_settings()
    directory = directory or load_directory(settings)

    current = _current_skills(assessment)
    return [_build_pathway(sector, current, directory) for sector in _choose_targets(assessment)]
