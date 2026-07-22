import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import DomainStatus


class Domain(BaseModel):
    __tablename__ = "domains"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    status: Mapped[DomainStatus] = mapped_column(
        Enum(DomainStatus, name="domain_status"), nullable=False, default=DomainStatus.PENDING
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    creator = relationship("User", back_populates="domains")
    scans = relationship("Scan", back_populates="domain", cascade="all, delete-orphan")
