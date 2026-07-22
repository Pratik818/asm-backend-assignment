import uuid
from datetime import UTC, datetime

from app.db.session import SessionLocal
from app.models.asset import Asset
from app.models.domain import Domain
from app.models.enums import DomainStatus, ScanStatus
from app.models.scan import Scan
from app.repositories.asset_repository import AssetRepository
from app.workers.celery_app import celery_app
from app.workers.dns_resolver import RECORD_TYPES, resolve_records


@celery_app.task(name="ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="discover_domain")
def discover_domain(scan_id: str) -> None:
    db = SessionLocal()
    try:
        scan = db.get(Scan, uuid.UUID(scan_id))
        if scan is None:
            return

        domain = db.get(Domain, scan.domain_id)

        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now(UTC)
        if domain is not None:
            domain.status = DomainStatus.RUNNING
        db.commit()

        try:
            assets = []
            if domain is not None:
                for record_type in RECORD_TYPES:
                    for value in resolve_records(domain.name, record_type):
                        assets.append(
                            Asset(
                                scan_id=scan.id,
                                domain_id=domain.id,
                                type=record_type,
                                value=value,
                            )
                        )
            AssetRepository(db).bulk_create(assets)
        except Exception as exc:
            scan.status = ScanStatus.FAILED
            scan.error_message = str(exc)
            scan.completed_at = datetime.now(UTC)
            if domain is not None:
                domain.status = DomainStatus.FAILED
            db.commit()
            return

        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.now(UTC)
        if domain is not None:
            domain.status = DomainStatus.COMPLETED
        db.commit()
    finally:
        db.close()
