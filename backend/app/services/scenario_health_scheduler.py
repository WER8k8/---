# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""场景模型健康定时巡检。"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.nvidia_scenario_health_service import probe_all_scenario_health
from app.services.scenario_health_store import load_health_snapshot, save_health_snapshot

logger = logging.getLogger("uj-admin.scenario_health_scheduler")


class ScenarioHealthScheduler:
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
            cls._instance._interval_hours = 0
        return cls._instance

    def start(
        self,
        check_hour: int = 7,
        check_minute: int = 0,
        interval_hours: int | None = None,
    ) -> dict[str, str]:
        """start。

        参数说明：
        :param self: 参数 self
        :param check_hour: 参数 check_hour
        :param check_minute: 参数 check_minute
        :param interval_hours: 参数 interval_hours
        :return: 返回处理结果。
        """
        if self._running:
            return {"status": "already_running"}

        self._running = True
        self._interval_hours = interval_hours or int(
            getattr(settings, "AI_SCENARIO_HEALTH_INTERVAL_HOURS", 0) or 0
        )
        threading.Thread(
            target=self._loop,
            args=(check_hour, check_minute),
            daemon=True,
        ).start()
        logger.info(
            "ScenarioHealthScheduler started (daily %02d:%02d, interval=%sh)",
            check_hour,
            check_minute,
            self._interval_hours,
        )
        return {"status": "started"}

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
            if self._interval_hours and self._interval_hours > 0:
                wait = self._interval_hours * 3600
            else:
                now = datetime.now()
                next_run = now.replace(
                    hour=check_hour, minute=check_minute, second=0, microsecond=0
                )
                if now >= next_run:
                    next_run += timedelta(days=1)
                wait = (next_run - now).total_seconds()

            time.sleep(max(wait, 60))
            if not self._running:
                break
            try:
                self.run_once()
            except Exception as exc:
                logger.exception("Scenario health scheduled run failed")
                self.errors.append(str(exc))

    def run_once(self) -> dict:
        """run_once。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            report = probe_all_scenario_health(db)
            report["trigger"] = "scheduler"
            save_health_snapshot(db, report)
            self.last_run = datetime.now(timezone.utc).isoformat()
            self.run_count += 1
            logger.info(
                "Scenario health snapshot saved: %s/%s healthy",
                report.get("healthy_count"),
                report.get("total"),
            )
            return report
        finally:
            db.close()

    def status(self) -> dict:
        """status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            snapshot = load_health_snapshot(db)
        finally:
            db.close()
        return {
            "running": self._running,
            "last_run": self.last_run,
            "run_count": self.run_count,
            "latest_snapshot": snapshot,
            "errors": self.errors[-5:],
        }


scenario_health_scheduler = ScenarioHealthScheduler()


def run_scenario_health_check() -> dict:
    """供 ops 手动/cron 调用。"""
    db = SessionLocal()
    try:
        report = probe_all_scenario_health(db)
        report["trigger"] = "manual"
        return save_health_snapshot(db, report)
    finally:
        db.close()
