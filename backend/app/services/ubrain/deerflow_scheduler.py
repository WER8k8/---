"""DeerFlow 定时调度 — 每日市场研究 + 与 Hermes 运维循环联动。"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.ubrain.deerflow_scheduled_service import (
    load_deerflow_schedule_snapshot,
    run_deerflow_pending_only,
    run_scheduled_deerflow_update,
)

logger = logging.getLogger("uj-admin.deerflow_scheduler")


class DeerflowScheduler:
    _instance = None
    _running = False
    def __new__(cls):
        """__new__。

        参数说明：
        :param cls: 参数 cls
        :return: 返回处理结果。
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.last_run = None
            cls._instance.run_count = 0
            cls._instance.errors: list[str] = []
        return cls._instance

    def start(self, *, bootstrap: bool = False) -> dict[str, str]:
        """start。

        参数说明：
        :param self: 参数 self
        :param bootstrap: 参数 bootstrap
        :return: 返回处理结果。
        """
        if self._running:
            return {"status": "already_running"}
        self._running = True
        hour = int(getattr(settings, "DEERFLOW_SCHEDULE_HOUR", 7) or 7)
        minute = int(getattr(settings, "DEERFLOW_SCHEDULE_MINUTE", 30) or 30)
        threading.Thread(target=self._loop, args=(hour, minute), daemon=True).start()
        if bootstrap:
            threading.Thread(target=self._bootstrap, daemon=True).start()
        logger.info(
            "DeerflowScheduler started daily=%02d:%02d bootstrap=%s",
            hour,
            minute,
            bootstrap,
        )
        return {"status": "started"}

    def _bootstrap(self) -> None:
        """_bootstrap。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        time.sleep(40)
        if not self._running:
            return
        try:
            self.run_pending_once(trigger="bootstrap")
        except Exception as exc:
            logger.exception("DeerFlow bootstrap pending failed")
            self.errors.append(str(exc))

    def stop(self) -> dict[str, str]:
        """stop。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._running = False
        return {"status": "stopped"}

    def _loop(self, check_hour: int, check_minute: int) -> None:
        """_loop。

        参数说明：
        :param self: 参数 self
        :param check_hour: 参数 check_hour
        :param check_minute: 参数 check_minute
        :return: 返回处理结果。
        """
        while self._running:
            now = datetime.now()
            next_run = now.replace(
                hour=check_hour, minute=check_minute, second=0, microsecond=0
            )
            if now >= next_run:
                next_run += timedelta(days=1)
            wait = (next_run - now).total_seconds()
            slept = 0.0
            while self._running and slept < wait:
                chunk = min(120.0, wait - slept)
                time.sleep(chunk)
                slept += chunk
            if not self._running:
                break
            try:
                self.run_scheduled_once(trigger="scheduler")
            except Exception as exc:
                logger.exception("DeerFlow scheduled run failed")
                self.errors.append(str(exc))

    def run_scheduled_once(self, *, trigger: str = "scheduler") -> dict:
        """run_scheduled_once。

        参数说明：
        :param self: 参数 self
        :param trigger: 参数 trigger
        :return: 返回处理结果。
        """
        from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
        if not try_acquire_scheduler_lock("deerflow_daily", ttl_seconds=3600):
            return {"skipped": True, "reason": "leader_lock_busy", "trigger": trigger}
        try:
            db = SessionLocal()
            try:
                report = run_scheduled_deerflow_update(db, trigger=trigger)
                self.last_run = report.get("saved_at")
                self.run_count += 1
                return report
            finally:
                db.close()
        finally:
            release_scheduler_lock("deerflow_daily")

    def run_pending_once(self, *, trigger: str = "scheduler") -> dict:
        """执行待处理作业（ORCH-31: 添加分布式锁防重复执行）"""
        from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
        # ORCH-31: 多实例防重复执行
        if not try_acquire_scheduler_lock("deerflow_pending", ttl_seconds=1800):
            return {"skipped": True, "reason": "leader_lock_busy", "trigger": trigger}
        db = SessionLocal()
        try:
            report = run_deerflow_pending_only(db, trigger=trigger)
            self.last_run = report.get("saved_at")
            self.run_count += 1
            return report
        finally:
            db.close()
            release_scheduler_lock("deerflow_pending")

    def status(self) -> dict:
        """status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        snap = load_deerflow_schedule_snapshot()
        return {
            "running": self._running,
            "last_run": self.last_run,
            "run_count": self.run_count,
            "schedule": {
                "hour": int(getattr(settings, "DEERFLOW_SCHEDULE_HOUR", 7) or 7),
                "minute": int(getattr(settings, "DEERFLOW_SCHEDULE_MINUTE", 30) or 30),
            },
            "latest_snapshot": snap,
            "errors": self.errors[-5:],
        }


deerflow_scheduler = DeerflowScheduler()
