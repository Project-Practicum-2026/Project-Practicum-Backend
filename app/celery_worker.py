from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.cargo.tasks", "app.routes.tasks"],
)

celery_app.conf.beat_schedule = {
    "sync-cargo-every-hour": {
        "task": "app.cargo.tasks.sync_cargo",
        "schedule": crontab(minute="0"),
    },
}
celery_app.conf.timezone = "UTC"
