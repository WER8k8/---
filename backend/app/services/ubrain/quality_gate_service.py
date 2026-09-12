"""DF-13：研究质量门 — 低分自动重跑（限频）。"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.deerflow_job import DeerflowJob
from app.models.ubrain_commercial_os import UbrainResearchInsight
from app.services.ubrain.deerflow_job_service import enqueue_job

DEFAULT_THRESHOLD = 0.45
MAX_RERUNS_PER_DAY = 2


def _threshold() -> float:
    """_threshold。
    :return: 返回处理结果。
    """
    raw = os.getenv("DEERFLOW_QUALITY_RERUN_THRESHOLD", "")
    try:
        return float(raw) if raw else DEFAULT_THRESHOLD
    except ValueError:
        return DEFAULT_THRESHOLD


def maybe_enqueue_quality_rerun(
    db: Session,
    *,
    tenant_id: str,
    source_job_id: str,
    intent: str,
    quality_score: float | None,
    original_message: str,
) -> dict[str, Any] | None:
    """maybe_enqueue_quality_rerun。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param source_job_id: 参数 source_job_id
    :param intent: 参数 intent
    :param quality_score: 参数 quality_score
    :param original_message: 参数 original_message
    :return: 返回处理结果。
    """
    if intent != "market_research":
        return None
    score = float(quality_score if quality_score is not None else 1.0)
    if score >= _threshold():
        return None

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    reruns = (
        db.query(DeerflowJob)
        .filter(
            DeerflowJob.tenant_id == tenant_id,
            DeerflowJob.intent == "market_research",
            DeerflowJob.created_at >= since,
            DeerflowJob.payload_json.like('%"quality_rerun": true%'),
        )
        .count()
    )
    if reruns >= MAX_RERUNS_PER_DAY:
        return {"skipped": True, "reason": "daily_rerun_limit", "quality_score": score}

    job = enqueue_job(
        db,
        tenant_id=tenant_id,
        intent="market_research",
        payload={
            "message": f"【质量重跑】{original_message[:200]}",
            "context": {"quality_rerun": True, "source_job_id": source_job_id},
        },
    )
    return {"rerun_job_id": job.id, "quality_score": score, "threshold": _threshold()}
