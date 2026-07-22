from sqlalchemy.orm import Session

from app.models.scan import Scan


class ScanRepository:
    def __init__(self, db: Session) -> None:
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
