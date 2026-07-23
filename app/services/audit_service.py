import uuid

from sqlalchemy.orm import Session

from app.models.enums import EventType
from app.models.event_log import EventLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(self, event_type: EventType, actor_id: uuid.UUID | None, metadata: dict | None = None):
        self.db.add(EventLog(event_type=event_type, user_id=actor_id, event_metadata=metadata))
        self.db.commit()
