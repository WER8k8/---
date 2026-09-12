"""UBrain / DeerFlow Celery 任务。"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)

# BUG-19: 分布式锁 TTL（秒）
_LOCK_TTL = 900


@shared_task(bind=True, name="deerflow_scheduled_daily", max_retries=2, default_retry_delay=300)
def deerflow_scheduled_daily(self):
    """deerflow_scheduled_daily。

    参数说明：
    :param self: 参数 self
    :return: 返回处理结果。
    """
    from app.core.database import SessionLocal
    from app.core.config import settings
    from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
    from app.services.ubrain.deerflow_scheduled_service import run_scheduled_deerflow_update
    if not getattr(settings, "DEERFLOW_SCHEDULER_ENABLED", True):
        return {"skipped": True, "reason": "scheduler_disabled"}
    if not try_acquire_scheduler_lock("deerflow_daily", ttl_seconds=3600):
        return {"skipped": True, "reason": "leader_lock_busy"}
    db = SessionLocal()
    try:
        return run_scheduled_deerflow_update(db, trigger="celery_daily")
    except Exception as exc:
        logger.exception("deerflow_scheduled_daily failed")
        raise self.retry(exc=exc) from exc
    finally:
        db.close()
        release_scheduler_lock("deerflow_daily")


@shared_task(bind=True, name="deerflow_run_pending", max_retries=1, default_retry_delay=120)
def deerflow_run_pending(self, limit: int = 10, lane: str = "tenant"):
    """DF-09：消费 DeerFlow 队列（tenant 主通道 / ops 运维通道）。"""
    from app.core.database import SessionLocal
    from app.core.config import settings
    from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
    from app.services.ubrain.deerflow_scheduled_service import run_deerflow_pending_only
    if lane == "tenant" and not settings.deerflow_tenant_celery_active:
        return {"skipped": True, "reason": "tenant_worker_disabled"}

    if not try_acquire_scheduler_lock(f"deerflow_run_pending_{lane}", ttl_seconds=_LOCK_TTL):
        logger.info("deerflow_run_pending lane=%s lock held by another instance, skipping", lane)
        return {"skipped": True, "reason": "leader_lock_busy"}
    db = SessionLocal()
    try:
        return run_deerflow_pending_only(
            db,
            trigger=f"celery_{lane}",
            limit=limit,
            lane=lane,
        )
    except Exception as exc:
        logger.exception("deerflow_run_pending failed lane=%s", lane)
        raise self.retry(exc=exc) from exc
    finally:
        db.close()
        release_scheduler_lock(f"deerflow_run_pending_{lane}")


@shared_task(bind=True, name="flywheel_feedback_sync_daily", max_retries=1, default_retry_delay=300)
def flywheel_feedback_sync_daily(self):
    """INT-04：每日同步销售反馈到 research_hints + PostHog。"""
    from app.core.database import SessionLocal
    from app.models.tenant import Tenant
    from app.services.ubrain.commercial_os_bridge import collect_sales_feedback
    from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
    if not try_acquire_scheduler_lock("flywheel_feedback_sync_daily", ttl_seconds=_LOCK_TTL):
        logger.info("flywheel_feedback_sync_daily lock held by another instance, skipping")
        return {"skipped": True, "reason": "leader_lock_busy"}
    db = SessionLocal()
    synced = 0
    try:
        tenants = db.query(Tenant).filter(Tenant.is_active.is_(True)).limit(200).all()
        for t in tenants:
            try:
                collect_sales_feedback(db, str(t.id))
                synced += 1
            except Exception:
                logger.warning("feedback sync skipped tenant=%s", t.id)
        return {"synced": synced, "tenant_count": len(tenants)}
    except Exception as exc:
        logger.exception("flywheel_feedback_sync_daily failed")
        raise self.retry(exc=exc) from exc
    finally:
        db.close()
        release_scheduler_lock("flywheel_feedback_sync_daily")
