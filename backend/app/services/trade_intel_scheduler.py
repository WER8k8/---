# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""出海参谋海关数据 — 每周定时从 Comtrade 刷新。"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.trade_intel_refresh_service import (
    load_refresh_snapshot,
    refresh_customs_from_comtrade,
)

logger = logging.getLogger("uj-admin.trade_intel_scheduler")


class TradeIntelScheduler:
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
        weekday = int(getattr(settings, "TRADE_INTEL_REFRESH_WEEKDAY", 0) or 0)
        hour = int(getattr(settings, "TRADE_INTEL_REFRESH_HOUR", 3) or 3)
        minute = int(getattr(settings, "TRADE_INTEL_REFRESH_MINUTE", 30) or 30)
        threading.Thread(
            target=self._loop,
            args=(weekday, hour, minute),
            daemon=True,
        ).start()
        if bootstrap:
            threading.Thread(target=self._bootstrap, daemon=True).start()
        logger.info(
            "TradeIntelScheduler started weekday=%s time=%02d:%02d bootstrap=%s",
            weekday,
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
        time.sleep(55)
        if not self._running:
            return
        snap = load_refresh_snapshot()
        if snap and snap.get("saved_at"):
            return
        try:
            self.run_once(trigger="bootstrap")
        except Exception as exc:
            logger.exception("Trade intel bootstrap refresh failed")
            self.errors.append(str(exc))

    def stop(self) -> dict[str, str]:
        """stop。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._running = False
        return {"status": "stopped"}

    def _next_weekly(self, weekday: int, hour: int, minute: int) -> datetime:
        """_next_weekly。

        参数说明：
        :param self: 参数 self
        :param weekday: 参数 weekday
        :param hour: 参数 hour
        :param minute: 参数 minute
        :return: 返回处理结果。
        """
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        days_ahead = (weekday - now.weekday()) % 7
        if days_ahead == 0 and now >= target:
            days_ahead = 7
        return target + timedelta(days=days_ahead)

    def _loop(self, weekday: int, hour: int, minute: int) -> None:
        """_loop。

        参数说明：
        :param self: 参数 self
        :param weekday: 参数 weekday
        :param hour: 参数 hour
        :param minute: 参数 minute
        :return: 返回处理结果。
        """
        while self._running:
            next_run = self._next_weekly(weekday, hour, minute)
            wait = (next_run - datetime.now()).total_seconds()
            slept = 0.0
            while self._running and slept < wait:
                chunk = min(120.0, wait - slept)
                time.sleep(chunk)
                slept += chunk
            if not self._running:
                break
            try:
                self.run_once(trigger="scheduler")
            except Exception as exc:
                logger.exception("Trade intel scheduled refresh failed")
                self.errors.append(str(exc))

    def run_once(self, *, trigger: str = "scheduler") -> dict:
        """run_once。

        参数说明：
        :param self: 参数 self
        :param trigger: 参数 trigger
        :return: 返回处理结果。
        """
        from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
        if not try_acquire_scheduler_lock("trade_intel_refresh", ttl_seconds=7200):
            return {"skipped": True, "reason": "leader_lock_busy", "trigger": trigger}
        try:
            db = SessionLocal()
            try:
                seed_db = bool(getattr(settings, "TRADE_INTEL_REFRESH_SEED_DB", True))
                report = refresh_customs_from_comtrade(
                    db=db,
                    seed_db=seed_db,
                    trigger=trigger,
                )
                self.last_run = report.get("saved_at")
                self.run_count += 1
                return report
            finally:
                db.close()
        finally:
            release_scheduler_lock("trade_intel_refresh")

    def status(self) -> dict:
        """status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "running": self._running,
            "last_run": self.last_run,
            "run_count": self.run_count,
            "schedule": {
                "weekday": int(getattr(settings, "TRADE_INTEL_REFRESH_WEEKDAY", 0) or 0),
                "hour": int(getattr(settings, "TRADE_INTEL_REFRESH_HOUR", 3) or 3),
                "minute": int(getattr(settings, "TRADE_INTEL_REFRESH_MINUTE", 30) or 30),
            },
            "latest_snapshot": load_refresh_snapshot() or {},
            "errors": self.errors[-5:],
        }


trade_intel_scheduler = TradeIntelScheduler()
