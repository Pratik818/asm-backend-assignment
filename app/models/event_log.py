import uuid

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import EventType


class EventLog(BaseModel):
    __tablename__ = "event_logs"

    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
