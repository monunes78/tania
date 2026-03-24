from celery import Celery
from src.config import settings

celery_app = Celery(
    "tania",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["src.workers.document_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
)
