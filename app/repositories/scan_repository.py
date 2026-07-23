import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import ScanStatus
from app.models.scan import Scan


class ScanRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, scan: Scan) -> Scan:
        self.db.add(scan)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(scan)
        return scan

    def get_running_for_domain(self, domain_id: uuid.UUID) -> Scan | None:
        return self.db.scalar(
            select(Scan).where(Scan.domain_id == domain_id, Scan.status == ScanStatus.RUNNING)
        )

    def list_by_domain(self, domain_id: uuid.UUID, page: int, limit: int) -> tuple[list[Scan], int]:
        query = select(Scan).where(Scan.domain_id == domain_id)
        count_query = select(func.count()).select_from(Scan).where(Scan.domain_id == domain_id)

        total = self.db.scalar(count_query) or 0
        items = list(
            self.db.scalars(
                query.order_by(Scan.created_at.desc()).offset((page - 1) * limit).limit(limit)
            )
        )
        return items, total
