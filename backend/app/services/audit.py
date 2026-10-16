from sqlalchemy.orm import Session

from app.database.models import AuditEvent


def audit(db: Session, action: str, actor: str, entity: str, detail: str):
    db.add(AuditEvent(action=action, actor=actor, entity=entity, detail=detail))

