from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.health import HealthResponse

health_router = APIRouter(tags=["health"])


@health_router.get("/health", response_model=HealthResponse)
def health_check(response: Response, db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return HealthResponse(status="error", database="unreachable")

    return HealthResponse(status="ok", database="connected")
