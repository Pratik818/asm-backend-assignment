import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import DomainStatus, UserRole
from app.models.user import User
from app.schemas.domain import DomainCreateRequest, DomainListResponse, DomainResponse
from app.services.domain_service import DomainService

domains_router = APIRouter(prefix="/domains", tags=["domains"])


@domains_router.get("", response_model=DomainListResponse)
def list_domains(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: DomainStatus | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    service = DomainService(db)
    items, total = service.list_domains(page=page, limit=limit, status=status, search=search)
    return DomainListResponse(items=items, page=page, limit=limit, total=total)


@domains_router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
def create_domain(
    command: DomainCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.ANALYST)),
):
    service = DomainService(db)
    return service.create_domain(command, created_by=current_user.id)


@domains_router.get("/{domain_id}", response_model=DomainResponse)
def get_domain(
    domain_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    service = DomainService(db)
    return service.get_domain(domain_id)


@domains_router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_domain(
    domain_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    service = DomainService(db)
    service.delete_domain(domain_id)
