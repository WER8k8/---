# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""摸金校尉 · Survival 周报调度 — 每周一推送飞书（全球累计 + 人格 + 大赛）。"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

logger = logging.getLogger("uj-admin.greedy_survival_digest_scheduler")


class GreedySurvivalDigestScheduler:
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
            cls._instance.last_result: dict[str, Any] | None = None
        return cls._instance

    def _poll_seconds(self) -> int:
        """_poll_seconds。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return max(int(getattr(settings, "HERMES_GREEDY_DIGEST_POLL_MINUTES", 30) or 30), 5) * 60

    def start(self) -> dict[str, str]:
        """start。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._running:
            return {"status": "already_running"}
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()
        logger.info("GreedySurvivalDigestScheduler started poll=%sm", self._poll_seconds() // 60)
        return {"status": "started"}

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
            try:
                self.tick()
            except Exception as exc:
                logger.exception("Greedy survival digest tick failed")
                self.errors.append(str(exc))
            slept = 0.0
            wait = float(self._poll_seconds())
            while self._running and slept < wait:
                chunk = min(60.0, wait - slept)
                time.sleep(chunk)
                slept += chunk

    def tick(self) -> dict[str, Any]:
        """tick。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        from app.services.hermes.greedy_survival_digest_service import is_weekly_digest_due
        tz = str(getattr(settings, "HERMES_GREEDY_DIGEST_TIMEZONE", "Asia/Shanghai") or "Asia/Shanghai")
        wd = int(getattr(settings, "HERMES_GREEDY_DIGEST_WEEKDAY", 0) or 0)
        hr = int(getattr(settings, "HERMES_GREEDY_DIGEST_HOUR", 9) or 9)
        due = is_weekly_digest_due(tz_name=tz, weekday=wd, hour=hr)
        if not due:
            return {"skipped": True, "reason": "not_due", "checked_at": datetime.now(timezone.utc).isoformat()}
        return self.run_once(trigger="scheduler")

    def run_once(self, *, trigger: str = "scheduler") -> dict[str, Any]:
        """run_once。

        参数说明：
        :param self: 参数 self
        :param trigger: 参数 trigger
        :return: 返回处理结果。
        """
        from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
        from app.services.hermes.greedy_survival_digest_service import send_survival_digest_feishu
        ttl = self._poll_seconds() + 600
        if trigger == "scheduler" and not try_acquire_scheduler_lock("greedy_survival_digest", ttl_seconds=ttl):
            return {"skipped": True, "reason": "leader_lock_busy", "trigger": trigger}

        try:
            result = send_survival_digest_feishu(respect_cooldown=(trigger == "scheduler"))
            self.last_run = datetime.now(timezone.utc).isoformat()
            self.run_count += 1
            self.last_result = {"sent": result.get("sent"), "trigger": trigger, "mood": (result.get("digest") or {}).get("mood")}
            if result.get("sent"):
                logger.info("Greedy survival digest sent [%s] mood=%s", trigger, self.last_result.get("mood"))
            return result
        finally:
            if trigger == "scheduler":
                release_scheduler_lock("greedy_survival_digest")

    def status(self) -> dict[str, Any]:
        """status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "running": self._running,
            "last_run": self.last_run,
            "run_count": self.run_count,
            "poll_minutes": self._poll_seconds() // 60,
            "weekday": int(getattr(settings, "HERMES_GREEDY_DIGEST_WEEKDAY", 0) or 0),
            "hour": int(getattr(settings, "HERMES_GREEDY_DIGEST_HOUR", 9) or 9),
            "timezone": str(getattr(settings, "HERMES_GREEDY_DIGEST_TIMEZONE", "Asia/Shanghai") or "Asia/Shanghai"),
            "last_result": self.last_result,
            "errors": self.errors[-5:],
        }


greedy_survival_digest_scheduler = GreedySurvivalDigestScheduler()
