"""Celery — 出海参谋海关数据定时刷新。"""

import logging

from celery import shared_task

from app.core.config import settings

logger = logging.getLogger("uj-admin.trade_intel_tasks")


@shared_task(bind=True, name="trade_intel_refresh_weekly", max_retries=2, default_retry_delay=600)
def trade_intel_refresh_weekly(self):
    """trade_intel_refresh_weekly。

    参数说明：
    :param self: 参数 self
    :return: 返回处理结果。
    """
    if not settings.trade_intel_scheduler_active:
        return {"skipped": True, "reason": "scheduler_disabled"}
    from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
    from app.services.trade_intel_scheduler import trade_intel_scheduler
    if not try_acquire_scheduler_lock("trade_intel_refresh", ttl_seconds=7200):
        return {"skipped": True, "reason": "leader_lock_busy"}
    try:
        return trade_intel_scheduler.run_once(trigger="celery_weekly")
    except Exception as exc:
        logger.exception("trade_intel_refresh_weekly failed")
        raise self.retry(exc=exc) from exc
    finally:
        release_scheduler_lock("trade_intel_refresh")
