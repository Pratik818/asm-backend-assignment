import uuid

from sqlalchemy import Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import AssetType


class Asset(BaseModel):
    __tablename__ = "assets"
    __table_args__ = (Index("ix_assets_domain_id_type", "domain_id", "type"),)

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[AssetType] = mapped_column(Enum(AssetType, name="asset_type"), nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)

    scan = relationship("Scan", back_populates="assets")
