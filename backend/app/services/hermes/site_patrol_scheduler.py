"""Hermes 7×24 巡站调度 — 只读维护，间隔可配置。"""

from __future__ import annotations

import logging
import threading
import time

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.hermes.site_patrol_service import run_site_patrol
from app.services.hermes.site_patrol_store import load_patrol_snapshot

logger = logging.getLogger("uj-admin.hermes_site_patrol_scheduler")


class HermesSitePatrolScheduler:
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

    def _interval_seconds(self) -> int:
        """_interval_seconds。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        minutes = int(getattr(settings, "HERMES_SITE_PATROL_INTERVAL_MINUTES", 15) or 15)
        return max(minutes, 5) * 60

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
        threading.Thread(target=self._loop, daemon=True).start()
        if bootstrap:
            threading.Thread(target=self._bootstrap, daemon=True).start()
        logger.info(
            "HermesSitePatrolScheduler started interval=%sm bootstrap=%s",
            self._interval_seconds() // 60,
            bootstrap,
        )
        return {"status": "started"}

    def _bootstrap(self) -> None:
        """_bootstrap。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        time.sleep(25)
        if not self._running:
            return
        try:
            self.run_once(trigger="bootstrap")
        except Exception as exc:
            logger.exception("Hermes site patrol bootstrap failed")
            self.errors.append(str(exc))

    def stop(self) -> dict[str, str]:
        """stop。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._running = False
        return {"status": "stopped"}

    def _loop(self) -> None:
        """_loop。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        while self._running:
            wait = float(self._interval_seconds())
            slept = 0.0
            while self._running and slept < wait:
                chunk = min(60.0, wait - slept)
                time.sleep(chunk)
                slept += chunk
            if not self._running:
                break
            try:
                self.run_once(trigger="scheduler")
            except Exception as exc:
                logger.exception("Hermes site patrol scheduled run failed")
                self.errors.append(str(exc))

    def run_once(self, *, trigger: str = "scheduler") -> dict:
        """run_once。

        参数说明：
        :param self: 参数 self
        :param trigger: 参数 trigger
        :return: 返回处理结果。
        """
        from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
        ttl = self._interval_seconds() + 120
        if not try_acquire_scheduler_lock("hermes_ops", ttl_seconds=ttl):
            return {"skipped": True, "reason": "leader_lock_busy", "trigger": trigger}
        try:
            db = SessionLocal()
            try:
                if settings.hermes_ops_autopilot_active:
                    from app.services.hermes.ops_autopilot import run_full_ops_cycle
                    report = run_full_ops_cycle(db, trigger=trigger)
                    patrol = report.get("patrol") or {}
                    self.last_run = report.get("saved_at") or patrol.get("saved_at")
                    self.run_count += 1
                    logger.info(
                        "Hermes ops autopilot [%s] patrol=%s pass=%s fail=%s tech=%s",
                        trigger,
                        patrol.get("overall_status"),
                        patrol.get("pass_count"),
                        patrol.get("fail_count"),
                        (report.get("tech_radar") or {}).get("high_impact_count"),
                    )
                    return report

                report = run_site_patrol(db, trigger=trigger)
                self.last_run = report.get("saved_at")
                self.run_count += 1
                logger.info(
                    "Hermes site patrol [%s] overall=%s pass=%s fail=%s",
                    trigger,
                    report.get("overall_status"),
                    report.get("pass_count"),
                    report.get("fail_count"),
                )
                return report
            finally:
                db.close()
        finally:
            release_scheduler_lock("hermes_ops")

    def status(self) -> dict:
        """status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            snapshot = load_patrol_snapshot(db)
        finally:
            db.close()
        return {
            "running": self._running,
            "last_run": self.last_run,
            "run_count": self.run_count,
            "interval_minutes": self._interval_seconds() // 60,
            "latest_snapshot": snapshot,
            "errors": self.errors[-5:],
        }


hermes_site_patrol_scheduler = HermesSitePatrolScheduler()


def run_site_patrol_manual() -> dict:
    """run_site_patrol_manual。
    :return: 返回处理结果。
    """
    db = SessionLocal()
    try:
        return run_site_patrol(db, trigger="manual")
    finally:
        db.close()
