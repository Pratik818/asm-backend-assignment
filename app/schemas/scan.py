from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ScanStatus


class ScanTriggerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: UUID = Field(validation_alias="id")
    status: ScanStatus


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: UUID = Field(validation_alias="id")
    status: ScanStatus
    started_at: datetime | None
    completed_at: datetime | None


class ScanListResponse(BaseModel):
    items: list[ScanResponse]
    page: int
    limit: int
    total: int
