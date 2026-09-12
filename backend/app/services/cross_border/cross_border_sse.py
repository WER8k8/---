"""跨境任务 SSE 事件流。"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.cross_border.cross_border_job_service import (
    get_cross_border_job,
    serialize_cross_border_job,
)

TERMINAL = frozenset({"done", "failed"})


async def stream_cross_border_job_events(
    db: Session,
    job_id: str,
    user: User,
    *,
    interval_sec: float = 1.5,
    timeout_sec: float = 600.0,
) -> AsyncIterator[str]:
    """SSE：推送任务进度直至终态。"""
    elapsed = 0.0
    while elapsed <= timeout_sec:
        task = get_cross_border_job(db, job_id, user)
        if not task:
            payload = {"status": "failed", "error": "任务不存在", "job_id": job_id}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            return
        snap = serialize_cross_border_job(task)
        yield f"data: {json.dumps(snap, ensure_ascii=False)}\n\n"
        if snap.get("status") in TERMINAL:
            return
        await asyncio.sleep(interval_sec)
        elapsed += interval_sec
        db.expire_all()
    payload = {"status": "failed", "error": "监听超时", "job_id": job_id}
    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
