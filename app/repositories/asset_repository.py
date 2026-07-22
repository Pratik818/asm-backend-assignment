from sqlalchemy.orm import Session

from app.models.asset import Asset


class AssetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def bulk_create(self, assets: list[Asset]) -> None:
        if not assets:
            return
        self.db.add_all(assets)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
