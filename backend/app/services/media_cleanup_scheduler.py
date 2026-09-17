# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""视频成品定时清理调度。"""

from __future__ import annotations

import logging
import threading
import time

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.media_retention_service import run_media_cleanup

logger = logging.getLogger("uj-admin.media_cleanup_scheduler")


class MediaCleanupScheduler:
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

    def start(self, interval_minutes: int | None = None) -> dict[str, str]:
        """start。

        参数说明：
        :param self: 参数 self
        :param interval_minutes: 参数 interval_minutes
        :return: 返回处理结果。
        """
        if self._running:
            return {"status": "already_running"}
        self._running = True
        minutes = interval_minutes or int(
            getattr(settings, "MEDIA_CLEANUP_INTERVAL_MINUTES", 15) or 15
        )
        threading.Thread(target=self._loop, args=(max(minutes, 5),), daemon=True).start()
        logger.info("MediaCleanupScheduler started (every %s min)", minutes)
        return {"status": "started"}

    def stop(self) -> dict[str, str]:
        """stop。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._running = False
        return {"status": "stopped"}

    def _loop(self, interval_minutes: int) -> None:
        """_loop。

        参数说明：
        :param self: 参数 self
        :param interval_minutes: 参数 interval_minutes
        :return: 返回处理结果。
        """
        while self._running:
            time.sleep(interval_minutes * 60)
            if not self._running:
                break
            try:
                self.run_once()
            except Exception as exc:
                logger.exception("Media cleanup scheduled run failed")
                self.errors.append(str(exc))

    def run_once(self) -> dict:
        """run_once。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            report = run_media_cleanup(db)
            self.last_run = report.get("checked_at")
            self.run_count += 1
            if report.get("purged_count"):
                logger.info(
                    "Media cleanup: purged %s files, freed ~%s bytes",
                    report.get("purged_count"),
                    report.get("bytes_freed"),
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
        return {
            "running": self._running,
            "last_run": self.last_run,
            "run_count": self.run_count,
            "errors": self.errors[-5:],
        }


media_cleanup_scheduler = MediaCleanupScheduler()
