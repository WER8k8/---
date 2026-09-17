# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DeerFlow 超管运维：全平台队列分页 + SLO 指标。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.deerflow_job import DeerflowJob
from app.services.ubrain.deerflow_job_service import serialize_job_with_steps


def list_ops_jobs(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 30,
    status: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """list_ops_jobs。

    参数说明：
    :param db: 参数 db
    :param page: 参数 page
    :param page_size: 参数 page_size
    :param status: 参数 status
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    q = db.query(DeerflowJob)
    if status:
        q = q.filter(DeerflowJob.status == status)
    if tenant_id:
        q = q.filter(DeerflowJob.tenant_id == tenant_id)
    total = q.count()
    rows = (
        q.order_by(DeerflowJob.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [serialize_job_with_steps(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def deerflow_slo_snapshot(db: Session, *, window_hours: int = 168) -> dict[str, Any]:
    """近 7 天排队时长与失败率。"""
    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    rows = (
        db.query(DeerflowJob)
        .filter(DeerflowJob.created_at >= since)
        .all()
    )
    total = len(rows)
    failed = sum(1 for r in rows if r.status == "failed")
    success = sum(1 for r in rows if r.status == "success")
    queue_secs: list[float] = []
    run_secs: list[float] = []
    for r in rows:
        if r.started_at and r.created_at:
            queue_secs.append((r.started_at - r.created_at).total_seconds())
        if r.finished_at and r.started_at:
            run_secs.append((r.finished_at - r.started_at).total_seconds())

    def _avg(vals: list[float]) -> float | None:
        """_avg。

        参数说明：
        :param vals: 参数 vals
        :return: 返回处理结果。
        """
        return round(sum(vals) / len(vals), 1) if vals else None

    counts: dict[str, int] = {}
    for st in ("queued", "running", "success", "failed"):
        counts[st] = db.query(DeerflowJob).filter(DeerflowJob.status == st).count()

    return {
        "window_hours": window_hours,
        "total_jobs": total,
        "success_count": success,
        "failed_count": failed,
        "failure_rate": round(failed / total, 4) if total else 0,
        "avg_queue_seconds": _avg(queue_secs),
        "avg_run_seconds": _avg(run_secs),
        "current_counts": counts,
    }
