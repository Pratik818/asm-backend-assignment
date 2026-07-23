import uuid

from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.enums import AssetType
from app.repositories.asset_repository import AssetRepository


class AssetService:
    def __init__(self, db: Session):
        self.asset_repository = AssetRepository(db)

    def list_assets(
        self,
        page: int,
        limit: int,
        domain_id: uuid.UUID | None,
        type: AssetType | None,
    ) -> tuple[list[Asset], int]:
        return self.asset_repository.list_paginated(
            page=page, limit=limit, domain_id=domain_id, type=type
        )
