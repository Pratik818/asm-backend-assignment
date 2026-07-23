import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import Pagination, get_current_user
from app.db.session import get_db
from app.models.enums import AssetType
from app.models.user import User
from app.schemas.asset import AssetListResponse
from app.services.asset_service import AssetService

assets_router = APIRouter(prefix="/assets", tags=["assets"])


@assets_router.get("", response_model=AssetListResponse)
def list_assets(
    domain_id: uuid.UUID | None = None,
    type: list[AssetType] | None = Query(default=None),
    pagination: Pagination = Depends(Pagination),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    service = AssetService(db)
    items, total = service.list_assets(
        page=pagination.page, limit=pagination.limit, domain_id=domain_id, type=type
    )
    return AssetListResponse(items=items, page=pagination.page, limit=pagination.limit, total=total)
