from celery import Celery

from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()

settings = get_settings()

celery_app = Celery(
    "asm",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)
