from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import staff_role
from app.core.safety import check_text
from app.database.models import Case, LearningProgress, utcnow
from app.database.session import get_db
from app.modules.base import CivicModule, Classification, extract_skills
from app.schemas.api import Recommendation, StrictModel
from app.services.audit import audit

LEARNING_STEPS = {"assess": "Reflect on existing skills", "course": "Discuss and select an approved course", "practice": "Complete a practical learning activity", "review": "Review progress with an adviser"}
router = APIRouter(prefix="/learning", tags=["learning"])


class ProgressInput(StrictModel):
    step_id: Literal["assess", "course", "practice", "review"]
    completed: bool
    note: str = Field(default="", max_length=500)

    @field_validator("note")
    @classmethod
    def safe_note(cls, value):
        return check_text(value)


def progress_data(case_id: int, db: Session):
    case = db.get(Case, case_id)
    if not case or case.module_id != "learning":
        raise HTTPException(status_code=404, detail="Learning case not found.")
    rows = {row.step_id: row for row in db.scalars(select(LearningProgress).where(LearningProgress.case_id == case_id))}
    steps = [{"id": key, "label": label, "completed": rows[key].completed if key in rows else False, "note": rows[key].note if key in rows else ""}
             for key, label in LEARNING_STEPS.items()]
    return {"case_id": case_id, "steps": steps, "completion_percent": round(100 * sum(step["completed"] for step in steps) / len(steps))}


@router.get("/progress/{case_id}")
def get_progress(case_id: int, db: Session = Depends(get_db), actor: str = Depends(staff_role)):
    return progress_data(case_id, db)


@router.post("/progress/{case_id}")
def update_progress(case_id: int, body: ProgressInput, db: Session = Depends(get_db), actor: str = Depends(staff_role)):
    progress_data(case_id, db)
    row = db.scalar(select(LearningProgress).where(LearningProgress.case_id == case_id, LearningProgress.step_id == body.step_id))
    if not row:
        row = LearningProgress(case_id=case_id, step_id=body.step_id)
        db.add(row)
    row.completed, row.note, row.updated_at = body.completed, body.note, utcnow()
    audit(db, "learning.progress", actor, f"case:{case_id}", f"Step {body.step_id} marked {'complete' if body.completed else 'pending'}.")
    db.commit()
    return progress_data(case_id, db)


class Learning(CivicModule):
    id = "learning"
    name = "Learning and Retraining Assistant"
    description = "Build a source-backed learning pathway and track reviewed progress."
    icon = "GraduationCap"
    input_hint = "Share what you can already do, your learning goal and available time."
    example_prompt = "I have customer service experience and want to learn digital skills for office work."
    capabilities = ["Skills reflection", "Course discovery", "Skills gap guidance", "Persisted progress tracking"]
    workflow_steps = ["Reflect on skills", "Find training sources", "Build a pathway", "Track adviser-reviewed progress"]
    resource_modules = ["learning"]
    router = router

    def classify(self, message):
        return Classification("Learning and retraining", "Skills and Learning", "Build a learning pathway", True)

    def recommend(self, message, resources):
        existing = set(extract_skills(message))
        return [Recommendation(title=r.title, description=r.description, next_steps=r.next_steps + ["Use the four-step progress plan with an adviser."],
                               match_score=None, skills_gap=sorted(set(r.skills) - existing)) for r, _ in resources[:3]]

    def explain(self, message):
        skills = extract_skills(message)
        return f"Skills reflected from your message: {', '.join(skills) if skills else 'none confidently identified'}. Course availability and suitability need adviser confirmation."

