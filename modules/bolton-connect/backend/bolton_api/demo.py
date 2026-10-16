"""Seed synthetic demonstration cases on first run.

In demo mode, if the case store is empty, we run each invented persona in
``demo_residents.json`` through the real pipeline and create a shared session and
adviser case. This is clearly-labelled synthetic data; no real personal data is
involved. Seeding is idempotent — it does nothing once cases exist.
"""
from __future__ import annotations

import json

from .assessment import assess
from .action_plan import build_action_plan
from .matching import match
from .pathways import generate_pathways
from .persistence import get_store
from .routes import _case_flags, _case_summary
from .schemas import AssessmentRequest, ResidentProfile
from .settings import Settings, get_settings


def seed_demo_cases(settings: Settings | None = None) -> int:
    settings = settings or get_settings()
    if not settings.demo_mode:
        return 0
    store = get_store(settings)
    if store.list_cases():
        return 0
    try:
        raw = json.loads(settings.demo_residents_path.read_text(encoding="utf-8"))
    except OSError:
        return 0

    created = 0
    for persona in raw.get("residents", []):
        try:
            profile = ResidentProfile(**persona.get("profile", {}))
            request = AssessmentRequest(text=persona["text"], profile=profile)
        except Exception:
            continue
        assessment = assess(request, settings)
        result = match(assessment, profile, settings)
        pathways = generate_pathways(assessment, settings)
        plan = build_action_plan(
            assessment, result, pathways, profile,
            resident_name=persona.get("name", "Resident"), settings=settings,
        )
        session_id = store.save_session(
            resident_name=persona.get("name", "Resident"),
            consent_save=True,
            consent_share=True,
            request=request.model_dump(mode="json"),
            result=plan.model_dump(mode="json"),
        )
        store.create_case(
            session_id=session_id,
            summary=f"[{persona.get('scenario', 'demo')}] " + _case_summary(assessment, result),
            needs_review=True,
            flags=_case_flags(assessment, result),
        )
        created += 1
    return created
