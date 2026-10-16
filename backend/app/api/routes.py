from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import actor_role, admin_role, staff_role
from app.core.safety import safe_excerpt
from app.core.settings import BOROUGHS
from app.database.models import AuditEvent, Case, Feedback, Resource, utcnow
from app.database.session import get_db
from app.evaluation.metrics import impact_report
from app.modules.registry import MODULES
from app.schemas.api import CaseUpdate, ChallengeConfig, DocumentInput, EnquiryInput, FeedbackInput
from app.services.audit import audit
from app.services.cases import case_data, create_case
from app.services.config import read_config, write_config
from app.services.seed import seed_demo

router = APIRouter()


def resource_data(resource: Resource):
    return {field: getattr(resource, field) for field in ["id", "title", "category", "module_id", "borough", "description", "content", "source_label", "source_url", "synthetic", "skills", "next_steps"]}


def config_data(request: Request):
    settings = request.app.state.settings
    return read_config(settings.challenge_config_path).model_dump(mode="json") | {"demo_mode": settings.demo_mode, "boroughs": BOROUGHS}


@router.get("/health")
def health(request: Request, db: Session = Depends(get_db)):
    db.execute(select(1))
    settings = request.app.state.settings
    provider = "compatible" if settings.llm_provider == "compatible" else "deterministic-demo" if settings.demo_mode else "deterministic-grounded"
    return {"status": "ok", "demo_mode": settings.demo_mode, "provider": provider}


@router.get("/config")
def configuration(request: Request):
    return config_data(request)


@router.put("/config")
def update_configuration(body: ChallengeConfig, request: Request, db: Session = Depends(get_db), actor: str = Depends(admin_role)):
    write_config(request.app.state.settings.challenge_config_path, body)
    audit(db, "config.updated", actor, "challenge", f"Borough {body.challenge.borough}; {len(body.challenge.selected_modules)} modules enabled; review threshold {body.escalation_threshold}.")
    db.commit()
    return config_data(request)


@router.get("/modules")
def modules(request: Request):
    enabled = read_config(request.app.state.settings.challenge_config_path).challenge.selected_modules
    return {"modules": [module.descriptor(module.id in enabled) for module in MODULES.values()]}


@router.get("/resources")
def resources(request: Request, module_id: str | None = None, q: str = Query(default="", max_length=300),
              borough: str | None = None, db: Session = Depends(get_db)):
    config = read_config(request.app.state.settings.challenge_config_path)
    if borough is not None and borough not in BOROUGHS:
        raise HTTPException(status_code=422, detail="Unknown borough.")
    if module_id is not None and module_id not in MODULES:
        raise HTTPException(status_code=422, detail="Unknown module id.")
    query = select(Resource).where(Resource.approved.is_(True), Resource.borough == (borough or config.challenge.borough))
    if module_id:
        query = query.where(Resource.module_id == module_id)
    else:
        query = query.where(Resource.module_id.in_(config.challenge.selected_modules))
    rows = list(db.scalars(query.order_by(Resource.id)))
    if q.strip():
        from app.ai.retrieval import tokens
        wanted = tokens(q)
        rows = [row for row in rows if q.strip().casefold() in (row.title + " " + row.description + " " + row.content).casefold()
                or wanted & tokens(row.title + " " + row.description + " " + row.content)]
    return {"resources": [resource_data(row) for row in rows[:100]]}


@router.post("/enquiries", status_code=201)
def enquire(body: EnquiryInput, request: Request, db: Session = Depends(get_db), actor: str = Depends(actor_role)):
    return case_data(create_case(body, request.app.state.settings, db, actor))


@router.post("/workspace/analyse", status_code=201)
def workspace(body: EnquiryInput, request: Request, db: Session = Depends(get_db), actor: str = Depends(staff_role)):
    return case_data(create_case(body, request.app.state.settings, db, actor))


@router.get("/cases")
def cases(status: Literal["new", "in_review", "resolved"] | None = None, module_id: str | None = None,
          db: Session = Depends(get_db), actor: str = Depends(staff_role)):
    query = select(Case)
    if status:
        query = query.where(Case.status == status)
    if module_id:
        if module_id not in MODULES:
            raise HTTPException(status_code=422, detail="Unknown module id.")
        query = query.where(Case.module_id == module_id)
    return {"cases": [case_data(case) for case in db.scalars(query.order_by(Case.id.desc()).limit(500))]}


def require_case(db: Session, case_id: int):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case


@router.get("/cases/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db), actor: str = Depends(staff_role)):
    return case_data(require_case(db, case_id))


@router.patch("/cases/{case_id}")
def review_case(case_id: int, body: CaseUpdate, db: Session = Depends(get_db), actor: str = Depends(staff_role)):
    case = require_case(db, case_id)
    case.status, case.review_note, case.updated_at = body.status, body.review_note, utcnow()
    audit(db, "case.reviewed", actor, f"case:{case_id}", f"Human reviewer changed status to {body.status}; a review note was recorded.")
    db.commit()
    db.refresh(case)
    return case_data(case)


@router.post("/cases/{case_id}/feedback")
def feedback(case_id: int, body: FeedbackInput, db: Session = Depends(get_db)):
    require_case(db, case_id)
    row = db.scalar(select(Feedback).where(Feedback.case_id == case_id))
    if row:
        row.rating = body.rating
    else:
        db.add(Feedback(case_id=case_id, rating=body.rating))
    audit(db, "case.feedback", "resident", f"case:{case_id}", "A bounded prototype rating was recorded.")
    db.commit()
    return {"status": "recorded"}


@router.get("/impact")
def impact(request: Request, db: Session = Depends(get_db), actor: str = Depends(staff_role)):
    return impact_report(db, request.app.state.settings)


@router.get("/audit")
def activity(db: Session = Depends(get_db), actor: str = Depends(admin_role)):
    return {"events": [{key: getattr(event, key) for key in ["id", "action", "actor", "entity", "created_at", "detail"]} for event in db.scalars(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(200))]}


@router.post("/documents", status_code=201)
def ingest_document(body: DocumentInput, request: Request, db: Session = Depends(get_db), actor: str = Depends(admin_role)):
    if not body.approved:
        raise HTTPException(status_code=422, detail="Only explicitly approved text may enter the retrieval catalogue.")
    if not body.synthetic and body.source_url is None:
        raise HTTPException(status_code=422, detail="A non-synthetic document requires an attributed HTTP(S) source URL.")
    module = MODULES[body.module_id]
    classification = module.classify(body.content)
    label = body.source_label
    if body.synthetic and "synthetic" not in label.lower() and "fictional" not in label.lower():
        label = ("Synthetic · " + label)[:180]
    resource = Resource(title=body.title, category=classification.category, module_id=body.module_id, borough=body.borough,
                        description=safe_excerpt(body.content, 220), content=body.content, source_label=label,
                        source_url=str(body.source_url) if body.source_url else None, synthetic=body.synthetic, approved=True, seed_record=False,
                        skills=[], next_steps=["Read the attributed source and confirm current availability.", "Ask trained staff to review any consequential next steps."])
    db.add(resource)
    db.flush()
    audit(db, "document.approved", actor, f"resource:{resource.id}", f"Approved bounded text for {body.module_id} in {body.borough}; {'synthetic' if body.synthetic else 'attributed external'} source.")
    db.commit()
    db.refresh(resource)
    return resource_data(resource)


@router.post("/demo/reset")
def reset_demo(request: Request, db: Session = Depends(get_db), actor: str = Depends(admin_role)):
    settings = request.app.state.settings
    if not settings.demo_mode:
        raise HTTPException(status_code=403, detail="Demo reset is disabled outside synthetic demonstration mode.")
    return {"status": "reset", "case_count": seed_demo(db, settings, reset=True)}

