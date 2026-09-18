# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""JobGateway — platform_jobs 队列读写（Celery ops 调度用）。

诚实降级：无表/无库时不抛未定义；任务侧捕获 JobNotFoundError。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class JobNotFoundError(Exception):
    """任务不存在。"""


class JobGateway:
    def __init__(self, db: Any = None) -> None:
        self._db = db

    def _session(self) -> Any:
        if self._db is not None and hasattr(self._db, "execute"):
            return self._db
        try:
            from app.core.database import SessionLocal
            return SessionLocal()
        except Exception:
            return None

    def get(self, job_id: str) -> dict[str, Any]:
        db = self._session()
        if db is None:
            raise JobNotFoundError(f"db_unavailable:{job_id}")
        try:
            from sqlalchemy import text
            row = db.execute(
                text("select * from platform_jobs where id::text = :id"),
                {"id": str(job_id)},
            ).mappings().first()
            if not row:
                raise JobNotFoundError(str(job_id))
            return dict(row)
        except JobNotFoundError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("JobGateway.get 失败: %s", exc)
            raise JobNotFoundError(f"lookup_failed:{job_id}") from exc

    def mark(
        self,
        job_id: str,
        status: str,
        *,
        result: Any = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        db = self._session()
        if db is None:
            logger.warning("JobGateway.mark 无库 job=%s status=%s", job_id, status)
            return
        try:
            from sqlalchemy import text
            import json as _json
            payload = _json.dumps(result, ensure_ascii=False, default=str) if result is not None else None
            db.execute(
                text(
                    "update platform_jobs set status=:s, updated_at=:t, "
                    "result_json=coalesce(:r, result_json), "
                    "error_code=coalesce(:ec, error_code), "
                    "error_message=coalesce(:em, error_message) "
                    "where id::text=:id"
                ),
                {
                    "s": status,
                    "t": datetime.now(timezone.utc),
                    "r": payload,
                    "ec": error_code,
                    "em": (error_message or "")[:500] if error_message else None,
                    "id": str(job_id),
                },
            )
            db.commit()
        except Exception as exc:  # noqa: BLE001
            try:
                db.rollback()
            except Exception:
                pass
            logger.warning("JobGateway.mark 失败 job=%s: %s", job_id, exc)
