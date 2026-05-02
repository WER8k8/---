from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "seo_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "check-keyword-rankings": {
            "task": "app.tasks.seo_tasks.check_all_keyword_rankings",
            "schedule": 86400.0,
        },
        "run-periodic-site-audit": {
            "task": "app.tasks.seo_tasks.run_site_audit",
            "schedule": 604800.0,
        },
    },
)
