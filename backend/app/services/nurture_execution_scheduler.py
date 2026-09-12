"""养号全链路调度器 — 互动执行 + 定时发布 + 状态升级 + 规则计划。"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.logging import get_logger

logger = get_logger(__name__)

# ORCH-04: 分布式锁 TTL（秒）
_LOCK_TTL = 600


class NurtureExecutionScheduler:
    """养号执行调度器（AiToEarn 对齐：规则 → 计划 → 真执行）。"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.scheduler: AsyncIOScheduler | None = None
        self._running = False

    def start(
        self,
        *,
        engagement_interval_minutes: int = 10,
        publish_interval_minutes: int = 5,
        plan_interval_minutes: int = 30,
        advance_interval_minutes: int = 60,
    ) -> None:
        """start。

        参数说明：
        :param self: 参数 self
        :param engagement_interval_minutes: 参数 engagement_interval_minutes
        :param publish_interval_minutes: 参数 publish_interval_minutes
        :param plan_interval_minutes: 参数 plan_interval_minutes
        :param advance_interval_minutes: 参数 advance_interval_minutes
        :return: 返回处理结果。
        """
        if self._running:
            logger.warning("NurtureExecutionScheduler already running")
            return

        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(
            self._run_engagement_worker,
            "interval",
            minutes=engagement_interval_minutes,
            id="nurture_engagement_worker",
            name="养号互动执行",
            replace_existing=True,
            max_instances=1,  # ORCH-01: 防止并发执行（多worker场景）
            coalesce=True,  # ORCH-01: 任务堆积时只执行最新一次
        )
        self.scheduler.add_job(
            self._run_scheduled_publish,
            "interval",
            minutes=publish_interval_minutes,
            id="nurture_scheduled_publish",
            name="养号定时发布",
            replace_existing=True,
            max_instances=1,  # ORCH-01: 防止并发执行（多worker场景）
            coalesce=True,  # ORCH-01: 任务堆积时只执行最新一次
        )
        self.scheduler.add_job(
            self._run_plan_engagements,
            "interval",
            minutes=plan_interval_minutes,
            id="nurture_plan_engagements",
            name="养号规则计划",
            replace_existing=True,
            max_instances=1,  # ORCH-01: 防止并发执行（多worker场景）
            coalesce=True,  # ORCH-01: 任务堆积时只执行最新一次
        )
        self.scheduler.add_job(
            self._run_auto_advance,
            "interval",
            minutes=advance_interval_minutes,
            id="nurture_auto_advance",
            name="养号状态升级",
            replace_existing=True,
            max_instances=1,  # ORCH-01: 防止并发执行（多worker场景）
            coalesce=True,  # ORCH-01: 任务堆积时只执行最新一次
        )
        self.scheduler.start()
        self._running = True
        logger.info(
            "NurtureExecutionScheduler started engage=%dm publish=%dm plan=%dm advance=%dm",
            engagement_interval_minutes,
            publish_interval_minutes,
            plan_interval_minutes,
            advance_interval_minutes,
        )

    def stop(self) -> None:
        """stop。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._running or not self.scheduler:
            return
        try:
            self.scheduler.shutdown(wait=False)
            self._running = False
            logger.info("NurtureExecutionScheduler stopped")
        except Exception as exc:
            logger.warning("NurtureExecutionScheduler stop failed: %s", exc)

    async def _run_engagement_worker(self) -> None:
        """_run_engagement_worker。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        lock_key = "orch:lock:engagement_worker"
        from app.core.cache import redis_client
        if redis_client:
            locked = redis_client.set(lock_key, "1", nx=True, ex=_LOCK_TTL)
            if not locked:
                logger.debug("Engagement worker lock held by another instance, skipping")
                return
        try:
            from app.services.nurture_execution_worker import execute_pending_engagements
            result = await execute_pending_engagements(limit=30)
            if result.get("executed", 0) > 0:
                logger.info(
                    "Nurture engagement executed=%d succeeded=%d failed=%d",
                    result.get("executed", 0),
                    result.get("succeeded", 0),
                    result.get("failed", 0),
                )
        except Exception as exc:
            logger.error("Nurture engagement worker failed: %s", exc, exc_info=True)
        finally:
            if redis_client:
                try:
                    redis_client.delete(lock_key)
                except Exception:
                    pass

    async def _run_scheduled_publish(self) -> None:
        """_run_scheduled_publish。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        lock_key = "orch:lock:scheduled_publish"
        from app.core.cache import redis_client
        if redis_client:
            locked = redis_client.set(lock_key, "1", nx=True, ex=_LOCK_TTL)
            if not locked:
                logger.debug("Scheduled publish lock held by another instance, skipping")
                return
        try:
            from app.tasks.scheduled_publish_worker import dispatch_pending_scheduled_publishes
            result = await dispatch_pending_scheduled_publishes()
            if result.get("dispatched", 0) > 0:
                logger.info(
                    "Scheduled publish dispatched=%d succeeded=%d failed=%d",
                    result.get("dispatched", 0),
                    result.get("succeeded", 0),
                    result.get("failed", 0),
                )
        except Exception as exc:
            logger.error("Scheduled publish worker failed: %s", exc, exc_info=True)
        finally:
            if redis_client:
                try:
                    redis_client.delete(lock_key)
                except Exception:
                    pass

    async def _run_plan_engagements(self) -> None:
        """_run_plan_engagements。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        lock_key = "orch:lock:plan_engagements"
        from app.core.cache import redis_client
        if redis_client:
            locked = redis_client.set(lock_key, "1", nx=True, ex=_LOCK_TTL)
            if not locked:
                logger.debug("Plan engagements lock held by another instance, skipping")
                return
        try:
            from app.core.database import SessionLocal
            from app.services.social_nurture_service import plan_daily_engagements
            db = SessionLocal()
            try:
                result = plan_daily_engagements(db, limit=40)
            finally:
                db.close()
            if result.get("planned", 0) > 0:
                logger.info("Nurture plan created %d pending engagements", result["planned"])
        except Exception as exc:
            logger.error("Nurture plan worker failed: %s", exc, exc_info=True)
        finally:
            if redis_client:
                try:
                    redis_client.delete(lock_key)
                except Exception:
                    pass

    async def _run_auto_advance(self) -> None:
        """_run_auto_advance。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        lock_key = "orch:lock:auto_advance"
        from app.core.cache import redis_client
        if redis_client:
            locked = redis_client.set(lock_key, "1", nx=True, ex=_LOCK_TTL)
            if not locked:
                logger.debug("Auto advance lock held by another instance, skipping")
                return
        try:
            from app.tasks.scheduled_publish_worker import auto_advance_all_nurture_cycles
            result = await auto_advance_all_nurture_cycles()
            if result.get("advanced", 0) > 0:
                logger.info(
                    "Nurture auto-advance checked=%d advanced=%d",
                    result.get("checked", 0),
                    result.get("advanced", 0),
                )
        except Exception as exc:
            logger.error("Nurture auto-advance failed: %s", exc, exc_info=True)
        finally:
            if redis_client:
                try:
                    redis_client.delete(lock_key)
                except Exception:
                    pass


nurture_execution_scheduler = NurtureExecutionScheduler()
