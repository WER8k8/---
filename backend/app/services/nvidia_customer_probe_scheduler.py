"""英伟达客户可用模型定时探测：默认每日 1:00 / 12:00 / 20:00（北京时间）。"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.nvidia_customer_probe_service import (
    parse_probe_slots,
    run_nvidia_customer_model_probe,
)
from app.services.nvidia_customer_probe_store import load_probe_snapshot

logger = logging.getLogger("uj-admin.nvidia_customer_probe_scheduler")


def _seconds_until_next_slot() -> float:
    """_seconds_until_next_slot。
    :return: 返回处理结果。
    """
    tz_name = getattr(settings, "NVIDIA_CUSTOMER_PROBE_TZ", "Asia/Shanghai") or "Asia/Shanghai"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Asia/Shanghai")

    now = datetime.now(tz)
    slots = parse_probe_slots()
    candidates: list[datetime] = []
    for hour, minute in slots:
        today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if today > now:
            candidates.append(today)
        candidates.append(today + timedelta(days=1))
    if not candidates:
        return 3600.0
    nxt = min(candidates)
    return max((nxt - now).total_seconds(), 60.0)


class NvidiaCustomerProbeScheduler:
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

    def start(self, *, bootstrap_probe: bool = False) -> dict[str, str]:
        """start。

        参数说明：
        :param self: 参数 self
        :param bootstrap_probe: 参数 bootstrap_probe
        :return: 返回处理结果。
        """
        if self._running:
            return {"status": "already_running"}
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()
        if bootstrap_probe:
            threading.Thread(target=self._bootstrap_probe, daemon=True).start()
        slots = parse_probe_slots()
        logger.info(
            "NvidiaCustomerProbeScheduler started slots=%s tz=%s bootstrap=%s",
            slots,
            getattr(settings, "NVIDIA_CUSTOMER_PROBE_TZ", "Asia/Shanghai"),
            bootstrap_probe,
        )
        return {"status": "started"}

    def _bootstrap_probe(self) -> None:
        """部署后尽快跑一次探测，不必等到下一个整点槽位。"""
        time.sleep(20)
        if not self._running:
            return
        try:
            self.run_once()
            logger.info("Nvidia customer probe bootstrap run completed")
        except Exception as exc:
            logger.exception("Nvidia customer probe bootstrap run failed")
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
            wait = _seconds_until_next_slot()
            logger.info("NvidiaCustomerProbeScheduler sleeping %.0fs until next slot", wait)
            slept = 0.0
            while self._running and slept < wait:
                chunk = min(60.0, wait - slept)
                time.sleep(chunk)
                slept += chunk
            if not self._running:
                break
            try:
                self.run_once()
            except Exception as exc:
                logger.exception("Nvidia customer probe scheduled run failed")
                self.errors.append(str(exc))

    def run_once(self) -> dict:
        """run_once。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            report = run_nvidia_customer_model_probe(db, trigger="scheduler")
            self.last_run = report.get("saved_at")
            self.run_count += 1
            logger.info(
                "Nvidia customer probe saved: %s/%s healthy",
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
            snapshot = load_probe_snapshot(db)
        finally:
            db.close()
        return {
            "running": self._running,
            "last_run": self.last_run,
            "run_count": self.run_count,
            "next_slots": [f"{h:02d}:{m:02d}" for h, m in parse_probe_slots()],
            "timezone": getattr(settings, "NVIDIA_CUSTOMER_PROBE_TZ", "Asia/Shanghai"),
            "latest_snapshot": snapshot,
            "errors": self.errors[-5:],
        }


nvidia_customer_probe_scheduler = NvidiaCustomerProbeScheduler()


def run_nvidia_customer_probe_manual() -> dict:
    """run_nvidia_customer_probe_manual。
    :return: 返回处理结果。
    """
    db = SessionLocal()
    try:
        return run_nvidia_customer_model_probe(db, trigger="manual")
    finally:
        db.close()
