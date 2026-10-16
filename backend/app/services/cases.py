from uuid import uuid4
from datetime import timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.orchestrator import analyse
from app.core.settings import Settings
from app.database.models import Case, Evaluation
from app.modules.registry import get_module
from app.schemas.api import EnquiryInput
from app.services.audit import audit
from app.services.config import read_config


def case_data(case: Case) -> dict:
    fields = ["id", "reference", "resident_name", "message", "module_id", "borough", "category", "priority", "status", "department", "created_at", "updated_at", "review_note", "analysis"]
    data = {field: getattr(case, field) for field in fields}
    for field in ["created_at", "updated_at"]:
        if data[field].tzinfo is None:
            data[field] = data[field].replace(tzinfo=timezone.utc)
    return data


def create_case(body: EnquiryInput, settings: Settings, db: Session, actor: str = "resident", *, commit: bool = True) -> Case:
    config = read_config(settings.challenge_config_path)
    if body.module_id not in config.challenge.selected_modules:
        raise HTTPException(status_code=409, detail="This module is disabled for the current challenge. Choose an enabled workflow.")
    borough = body.borough or config.challenge.borough
    module = get_module(body.module_id)
    analysis, classification, priority = analyse(body.message, borough, module, settings, config, db)
    case = Case(reference=f"CF-{uuid4().hex[:10].upper()}", resident_name=body.resident_name, message=body.message,
                module_id=body.module_id, borough=borough, category=classification.category, department=classification.department,
                priority=priority, status="in_review" if analysis.needs_human_review else "new", analysis=analysis.model_dump(mode="json"))
    db.add(case)
    db.flush()
    db.add(Evaluation(case_id=case.id, processing_ms=analysis.processing_ms, confidence=analysis.confidence,
                      source_count=len(analysis.sources), escalated=analysis.needs_human_review, provider=analysis.provider,
                      criteria=[criterion.model_dump() for criterion in module.evaluate(body.message, analysis)]))
    audit(db, "case.created", actor, f"case:{case.id}", f"Module {body.module_id}; {len(analysis.sources)} approved sources; human review {'required' if analysis.needs_human_review else 'not triggered'}.")
    if commit:
        db.commit()
        db.refresh(case)
    return case

