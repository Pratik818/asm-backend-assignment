import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.auth import auth_router
from app.api.v1.domains import domains_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.session import engine
from app.workers.tasks import ping

configure_logging()

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    logger.info("Database connectivity verified")

    ping.delay().get(timeout=5)
    logger.info("Celery worker connectivity verified")

    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(domains_router)
