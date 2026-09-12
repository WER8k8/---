"""摸金校尉 · 搞钱闭环日调度 — 与 SaaS Hermes 巡站调度隔离。"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Any

from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger("uj-admin.greedy_revenue_loop_scheduler")


class GreedyRevenueLoopScheduler:
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
            cls._instance.last_report: dict[str, Any] | None = None
        return cls._instance

    def _interval_seconds(self) -> int:
        """_interval_seconds。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        hours = int(getattr(settings, "HERMES_GREEDY_REVENUE_LOOP_INTERVAL_HOURS", 24) or 24)
        return max(hours, 1) * 3600

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
            "GreedyRevenueLoopScheduler started interval=%sh bootstrap=%s",
            self._interval_seconds() // 3600,
            bootstrap,
        )
        return {"status": "started"}

    def _bootstrap(self) -> None:
        """_bootstrap。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        time.sleep(45)
        if not self._running:
            return
        try:
            self.run_once(trigger="bootstrap")
        except Exception as exc:
            logger.exception("Greedy revenue loop bootstrap failed")
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
                chunk = min(120.0, wait - slept)
                time.sleep(chunk)
                slept += chunk
            if not self._running:
                break
            try:
                self.run_once(trigger="scheduler")
            except Exception as exc:
                logger.exception("Greedy revenue loop scheduled run failed")
                self.errors.append(str(exc))

    def run_once(self, *, trigger: str = "scheduler") -> dict[str, Any]:
        """run_once。

        参数说明：
        :param self: 参数 self
        :param trigger: 参数 trigger
        :return: 返回处理结果。
        """
        from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
        ttl = self._interval_seconds() + 300
        if not try_acquire_scheduler_lock("greedy_mojin", ttl_seconds=ttl):
            return {"skipped": True, "reason": "leader_lock_busy", "trigger": trigger}

        try:
            from app.services.hermes.greedy_contest_memory_service import tick_endurance_arena
            tick_endurance_arena(trigger=f"revenue_loop_{trigger}")
            from app.services.hermes.greedy_revenue_loop_service import run_greedy_revenue_loop_async
            db = SessionLocal()
            try:
                report = asyncio.run(
                    run_greedy_revenue_loop_async(
                        db,
                        trigger=trigger,
                        locale=str(getattr(settings, "HERMES_GREEDY_DEFAULT_LOCALE", "global") or "global"),
                        survival_goal_cny=int(
                            (getattr(settings, "PLATFORM_SURVIVAL_DAILY_TARGET_CNY_MINOR", 100000) or 100000)
                            // 100
                        ),
                    )
                )
                self.last_run = report.get("generated_at")
                self.last_report = {
                    "loop_complete": report.get("loop_complete"),
                    "stages": len(report.get("stages") or []),
                    "trigger": trigger,
                }
                self.run_count += 1
                stages = report.get("stages") or []
                s6 = stages[-1] if stages else {}
                pulse = (s6.get("survival_pulse") or {}) if isinstance(s6, dict) else {}
                logger.info(
                    "Greedy revenue loop [%s] stages=%s kpi_pct=%s",
                    trigger,
                    len(stages),
                    pulse.get("progress_pct"),
                )
                return report
            finally:
                db.close()
        finally:
            release_scheduler_lock("greedy_mojin")

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
            "interval_hours": self._interval_seconds() // 3600,
            "last_report": self.last_report,
            "errors": self.errors[-5:],
            "codename": "摸金校尉",
        }


greedy_revenue_loop_scheduler = GreedyRevenueLoopScheduler()
