import re
import uuid

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import DomainStatus

FQDN_PATTERN = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))+$")


class DomainCreateRequest(BaseModel):
    domain: str

    @field_validator("domain")
    @classmethod
    def _validate_domain(cls, v: str) -> str:
        v = v.strip().lower()
        if not FQDN_PATTERN.match(v):
            raise ValueError("Must be a syntactically valid FQDN")
        return v


class DomainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: DomainStatus


class DomainListResponse(BaseModel):
    items: list[DomainResponse]
    page: int
    limit: int
    total: int
