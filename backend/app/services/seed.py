from datetime import datetime, timedelta, timezone
import json

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.settings import BOROUGHS, PROJECT_ROOT, Settings
from app.database.models import AuditEvent, Case, Evaluation, Feedback, LearningProgress, Resource
from app.schemas.api import EnquiryInput
from app.services.audit import audit
from app.services.cases import create_case
from app.services.config import read_config


def seed_demo(db: Session, settings: Settings, *, reset: bool = False) -> int:
    if not settings.demo_mode:
        raise ValueError("Synthetic reset and seed are only allowed in demo mode.")
    if not reset and db.scalar(select(func.count(Resource.id)).where(Resource.seed_record.is_(True))):
        return db.scalar(select(func.count(Case.id))) or 0
    if reset:
        for model in [LearningProgress, Feedback, Evaluation, AuditEvent, Case, Resource]:
            db.execute(delete(model))
        db.flush()
    catalog = json.loads((PROJECT_ROOT / "data" / "synthetic" / "resources.json").read_text())
    for borough in BOROUGHS:
        for item in catalog:
            db.add(Resource(title=item["title"], category=item["category"], module_id=item["module_id"], borough=borough,
                            description=item["description"], content=item["content"],
                            source_label=f"Adjust AI fictional demonstration catalogue · {borough}", source_url=None,
                            synthetic=True, approved=True, seed_record=True, skills=item["skills"], next_steps=item["next_steps"]))
    db.flush()
    config = read_config(settings.challenge_config_path)
    cases = json.loads((PROJECT_ROOT / "data" / "synthetic" / "enquiries.json").read_text())
    deterministic_settings = settings.model_copy(update={"llm_provider": "deterministic"})
    anchor = datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0)
    created = 0
    for index, item in enumerate(cases, 1):
        if item["module_id"] not in config.challenge.selected_modules:
            continue
        case = create_case(EnquiryInput(message=item["message"], module_id=item["module_id"], resident_name=item["resident_name"],
                                       borough=config.challenge.borough), deterministic_settings, db, "demo-seed", commit=False)
        case.reference = f"CF-DEMO-{index:04d}"
        case.seed_record = True
        case.created_at = anchor - timedelta(days=item["days_ago"], minutes=10 * index)
        case.updated_at = case.created_at + timedelta(minutes=4)
        case.status, case.review_note = item["status"], item["review_note"]
        if case.status == "resolved":
            db.add(Feedback(case_id=case.id, rating=4))
        if case.module_id == "learning":
            db.add(LearningProgress(case_id=case.id, step_id="assess", completed=True, note="Synthetic skills reflection completed."))
        db.flush()
        created += 1
    audit(db, "demo.reset" if reset else "demo.seed", "admin" if reset else "system", "demo", f"Loaded {created} fictional cases and {len(catalog) * len(BOROUGHS)} labelled fictional resources.")
    db.commit()
    return created

