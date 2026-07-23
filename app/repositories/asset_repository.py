import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.asset import Asset
from app.models.enums import AssetType


class AssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_create(self, assets: list[Asset]):
        if not assets:
            return
        self.db.add_all(assets)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def list_paginated(
        self,
        page: int,
        limit: int,
        domain_id: uuid.UUID | None = None,
        type: list[AssetType] | None = None,
    ) -> tuple[list[Asset], int]:
        query = select(Asset).options(joinedload(Asset.domain))
        count_query = select(func.count()).select_from(Asset)

        if domain_id is not None:
            query = query.where(Asset.domain_id == domain_id)
            count_query = count_query.where(Asset.domain_id == domain_id)
        if type:
            query = query.where(Asset.type.in_(type))
            count_query = count_query.where(Asset.type.in_(type))

        total = self.db.scalar(count_query) or 0
        items = list(
            self.db.scalars(
                query.order_by(Asset.created_at.desc()).offset((page - 1) * limit).limit(limit)
            )
        )
        return items, total
