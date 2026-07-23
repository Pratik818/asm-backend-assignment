from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import AssetType


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    domain: str
    type: AssetType
    value: str

    @field_validator("domain", mode="before")
    @classmethod
    def _extract_domain_name(cls, v: object) -> object:
        return v.name if hasattr(v, "name") else v


class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    page: int
    limit: int
    total: int
