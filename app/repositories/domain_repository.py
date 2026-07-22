import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.domain import Domain
from app.models.enums import DomainStatus


class DomainRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_name(self, name: str) -> Domain | None:
        return self.db.scalar(select(Domain).where(Domain.name == name))

    def get_by_id(self, domain_id: uuid.UUID) -> Domain | None:
        return self.db.scalar(select(Domain).where(Domain.id == domain_id))

    def create(self, domain: Domain) -> Domain:
        self.db.add(domain)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(domain)
        return domain

    def delete(self, domain: Domain) -> None:
        self.db.delete(domain)
        self.db.commit()

    def list_paginated(
        self,
        page: int,
        limit: int,
        status: DomainStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[Domain], int]:
        query = select(Domain)
        count_query = select(func.count()).select_from(Domain)

        if status is not None:
            query = query.where(Domain.status == status)
            count_query = count_query.where(Domain.status == status)
        if search:
            pattern = f"%{search}%"
            query = query.where(Domain.name.ilike(pattern))
            count_query = count_query.where(Domain.name.ilike(pattern))

        total = self.db.scalar(count_query) or 0
        items = list(
            self.db.scalars(
                query.order_by(Domain.created_at.desc()).offset((page - 1) * limit).limit(limit)
            )
        )
        return items, total
