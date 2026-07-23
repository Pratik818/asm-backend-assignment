import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.domain import Domain
from app.models.enums import DomainStatus, ScanStatus
from app.models.scan import Scan
from app.repositories.domain_repository import DomainRepository
from app.repositories.scan_repository import ScanRepository
from app.schemas.domain import DomainCreateRequest
from app.workers.tasks import discover_domain


class DomainService:
    def __init__(self, db: Session):
        self.domain_repository = DomainRepository(db)
        self.scan_repository = ScanRepository(db)

    def create_domain(self, command: DomainCreateRequest, created_by: uuid.UUID) -> Domain:
        if self.domain_repository.get_by_name(command.domain):
            raise AppException(
                "Domain already registered", status_code=409, error_code="DOMAIN_ALREADY_EXISTS"
            )

        domain = Domain(name=command.domain, status=DomainStatus.PENDING, created_by=created_by)
        try:
            domain = self.domain_repository.create(domain)
        except IntegrityError as exc:
            raise AppException(
                "Domain already registered", status_code=409, error_code="DOMAIN_ALREADY_EXISTS"
            ) from exc

        scan = self.scan_repository.create(
            Scan(domain_id=domain.id, status=ScanStatus.PENDING, triggered_by=created_by)
        )
        discover_domain.delay(str(scan.id))

        return domain

    def get_domain(self, domain_id: uuid.UUID) -> Domain:
        domain = self.domain_repository.get_by_id(domain_id)
        if domain is None:
            raise AppException("Domain not found", status_code=404, error_code="DOMAIN_NOT_FOUND")
        return domain

    def list_domains(
        self, page: int, limit: int, status: DomainStatus | None, search: str | None
    ) -> tuple[list[Domain], int]:
        return self.domain_repository.list_paginated(
            page=page, limit=limit, status=status, search=search
        )

    def delete_domain(self, domain_id: uuid.UUID):
        domain = self.get_domain(domain_id)
        self.domain_repository.delete(domain)
