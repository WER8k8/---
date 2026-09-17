# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""开发环境运维自动驾驶 — 周期性健康探针，无需 Owner 开口。"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("uj-admin.ops_autopilot")

_PROBE_PATHS = (
    "/api/v1/health",
    "/api/v1/health/ready",
)


class OpsAutopilotScheduler:
    """本地 dev：每 N 分钟探针；失败写日志（SRE Lane 可读）。"""
    def __init__(self) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_ok = True
        self._last_report: dict[str, Any] = {}

    @property
    def interval_seconds(self) -> int:
        """interval_seconds。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        minutes = int(getattr(settings, "OPS_AUTOPILOT_INTERVAL_MINUTES", 120) or 120)
        return max(minutes, 15) * 60

    def start(self) -> None:
        """start。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="ops-autopilot", daemon=True)
        self._thread.start()
        logger.info("OpsAutopilotScheduler started interval=%ss", self.interval_seconds)

    def stop(self) -> None:
        """stop。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._stop.set()

    def status(self) -> dict[str, Any]:
        """status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "running": bool(self._thread and self._thread.is_alive()),
            "last_ok": self._last_ok,
            "interval_seconds": self.interval_seconds,
            "last_report": self._last_report,
        }

    def _loop(self) -> None:
        """_loop。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        time.sleep(30)
        while not self._stop.is_set():
            try:
                self._last_report = self.run_probe()
                self._last_ok = bool(self._last_report.get("ok"))
                if not self._last_ok:
                    logger.warning(
                        "Ops autopilot probe FAIL: %s — run scripts/start-dev-admin.ps1",
                        self._last_report.get("failures"),
                    )
            except Exception as exc:
                self._last_ok = False
                logger.warning("Ops autopilot probe error: %s", exc)
            self._stop.wait(self.interval_seconds)

    def run_probe(self) -> dict[str, Any]:
        """run_probe。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        base = (getattr(settings, "PUBLIC_API_BASE", None) or "http://127.0.0.1:8001").rstrip("/")
        checks: list[dict[str, Any]] = []
        failures: list[str] = []
        with httpx.Client(timeout=8.0) as client:
            for path in _PROBE_PATHS:
                url = f"{base}{path}"
                t0 = time.perf_counter()
                try:
                    r = client.get(url)
                    ms = int((time.perf_counter() - t0) * 1000)
                    ok = r.status_code == 200
                    checks.append({"path": path, "ok": ok, "status": r.status_code, "ms": ms})
                    if not ok:
                        failures.append(path)
                except Exception as exc:
                    ms = int((time.perf_counter() - t0) * 1000)
                    checks.append({"path": path, "ok": False, "ms": ms, "error": str(exc)[:80]})
                    failures.append(path)
        return {"ok": len(failures) == 0, "checks": checks, "failures": failures, "base": base}


ops_autopilot_scheduler = OpsAutopilotScheduler()
