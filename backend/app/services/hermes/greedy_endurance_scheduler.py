"""7×24 持久耐力赛调度 — 每小时检查 30 天擂台是否满期并轮转。"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from app.core.config import settings

logger = logging.getLogger("uj-admin.greedy_endurance_scheduler")


class GreedyEnduranceScheduler:
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
            cls._instance.last_tick = None
            cls._instance.tick_count = 0
            cls._instance.errors: list[str] = []
            cls._instance.last_rollover = None
        return cls._instance

    def _interval_seconds(self) -> int:
        """_interval_seconds。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        minutes = int(getattr(settings, "HERMES_GREEDY_ENDURANCE_TICK_MINUTES", 60) or 60)
        return max(minutes, 5) * 60

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
        logger.info(
            "GreedyEnduranceScheduler started (7x24 tick=%sm)",
            self._interval_seconds() // 60,
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
                logger.exception("Greedy endurance tick failed")
                self.errors.append(str(exc))
            slept = 0.0
            wait = float(self._interval_seconds())
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
        from app.services.hermes.greedy_contest_memory_service import tick_endurance_arena
        result = tick_endurance_arena(trigger="scheduler_7x24")
        self.last_tick = result.get("checked_at")
        self.tick_count += 1
        if result.get("rollover"):
            self.last_rollover = result.get("rollover")
            logger.info(
                "Arena rollover %s → %s",
                result.get("closed_arena_id"),
                result.get("new_arena_id"),
            )
        return result

    def status(self) -> dict[str, Any]:
        """status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        from app.services.hermes.greedy_contest_memory_service import get_endurance_status
        return {
            "running": self._running,
            "tick_count": self.tick_count,
            "interval_minutes": self._interval_seconds() // 60,
            "last_tick": self.last_tick,
            "last_rollover": self.last_rollover,
            "errors": self.errors[-5:],
            "endurance": get_endurance_status(),
        }


greedy_endurance_scheduler = GreedyEnduranceScheduler()
