from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.health import HealthResponse
from app.workers.tasks import ping

health_router = APIRouter(tags=["health"])


@health_router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception:
        database_status = "error"

    try:
        ping.delay().get(timeout=5)
        celery_status = "ok"
    except Exception:
        celery_status = "error"

    overall_status = "ok" if database_status == "ok" and celery_status == "ok" else "degraded"
    return HealthResponse(status=overall_status, database=database_status, celery=celery_status)
