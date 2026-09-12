"""跨境语言桥 Celery 任务。"""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="cross_border.run_job",
    max_retries=2,
    default_retry_delay=60,
    queue="cross_border",
)
def cross_border_run_job(self, job_id: str):
    """cross_border_run_job。

    参数说明：
    :param self: 参数 self
    :param job_id: 参数 job_id
    :return: 返回处理结果。
    """
    from app.core.database import SessionLocal
    from app.services.cross_border.cross_border_worker import run_cross_border_job
    db = SessionLocal()
    try:
        return run_cross_border_job(db, job_id)
    except Exception as exc:
        logger.exception("cross_border_run_job failed %s", job_id)
        raise self.retry(exc=exc) from exc
    finally:
        db.close()


def dispatch_by_job_id(job_id: str) -> bool:
    """尝试 Celery 入队；成功返回 True。"""
    from app.core.config import settings
    if not settings.REDIS_ENABLED:
        return False
    broker = (settings.CELERY_BROKER_URL or "").strip()
    if not broker:
        return False
    cross_border_run_job.delay(job_id)
    return True
