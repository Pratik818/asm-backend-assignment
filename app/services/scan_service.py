import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.enums import ScanStatus
from app.models.scan import Scan
from app.repositories.domain_repository import DomainRepository
from app.repositories.scan_repository import ScanRepository
from app.workers.tasks import discover_domain


class ScanService:
    def __init__(self, db: Session):
        self.domain_repository = DomainRepository(db)
        self.scan_repository = ScanRepository(db)

    def trigger_scan(self, domain_id: uuid.UUID, triggered_by: uuid.UUID) -> Scan:
        domain = self.domain_repository.get_by_id(domain_id)
        if domain is None:
            raise AppException("Domain not found", status_code=404, error_code="DOMAIN_NOT_FOUND")

        if self.scan_repository.get_running_for_domain(domain_id) is not None:
            raise AppException(
                "A scan is already running for this domain",
                status_code=409,
                error_code="SCAN_ALREADY_RUNNING",
            )

        scan = self.scan_repository.create(
            Scan(domain_id=domain_id, status=ScanStatus.PENDING, triggered_by=triggered_by)
        )
        discover_domain.delay(str(scan.id))
        return scan

    def list_scans(self, domain_id: uuid.UUID, page: int, limit: int) -> tuple[list[Scan], int]:
        domain = self.domain_repository.get_by_id(domain_id)
        if domain is None:
            raise AppException("Domain not found", status_code=404, error_code="DOMAIN_NOT_FOUND")

        return self.scan_repository.list_by_domain(domain_id, page=page, limit=limit)
