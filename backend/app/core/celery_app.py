from celery import Celery

from app.config import settings

celery_app = Celery(
    "smartbid_ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.document_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
)
