"""GEO Rank Guard 探针 — 司令部 / Celery / Hermes 告警共用。"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.core.config import settings
from app.services.rum_metrics_service import rum_for_rank_guard
from app.services.geo_rank_guard import GEORankGuard, GuardMetrics

logger = logging.getLogger("uj-admin.geo_rank_guard_probe")

SNAPSHOT_KEY = "geo:rank_guard:latest"
SNAPSHOT_TTL = 86400 * 7


def _latest_seo_audit_score(db: Session) -> float | None:
    """_latest_seo_audit_score。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    try:
        from app.models.seo import SiteAudit
        row = db.query(SiteAudit).order_by(SiteAudit.created_at.desc()).first()
        if row and row.score is not None:
            return float(row.score)
    except Exception:
        pass
    return None


def _geo_indexed_rate(db: Session) -> float | None:
    """_geo_indexed_rate。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    try:
        from app.models.content import InclusionStatus
        total = db.query(InclusionStatus).count()
        if not total:
            return None
        included = (
            db.query(InclusionStatus)
            .filter(InclusionStatus.is_included.is_(True))
            .count()
        )
        return round(included / total, 4)
    except Exception:
        return None


def run_rank_guard_probe(db: Session, *, trigger: str = "scheduler") -> dict[str, Any]:
    """轻量 Rank Guard 评估（收录率 + SEO 审计分 + 默认性能基线）。"""
    seo_score = _latest_seo_audit_score(db)
    geo_rate = _geo_indexed_rate(db)
    rum = rum_for_rank_guard(db)
    metrics = GuardMetrics(
        lcp_ms=int(rum["lcp_ms"]),
        inp_ms=int(rum["inp_ms"]),
        error_rate=float(rum["error_rate"]),
        inquiry_rate_delta=0.0,
        rank_signal_delta=0.0,
        seo_audit_score=seo_score,
        geo_indexed_rate=geo_rate,
    )
    guard = GEORankGuard()
    result = guard.evaluate(metrics)
    body: dict[str, Any] = {
        "trigger": trigger,
        "passed": result.passed,
        "blocked_reasons": result.blocked_reasons,
        "warning_reasons": result.warning_reasons,
        "checked_at": result.checked_at,
        "message": guard.format_blocked_message(result),
        "metrics": {
            "seo_audit_score": seo_score,
            "geo_indexed_rate": geo_rate,
            "lcp_ms": metrics.lcp_ms,
            "inp_ms": metrics.inp_ms,
            "error_rate": metrics.error_rate,
            "rum_source": rum.get("source"),
            "rum_samples": rum.get("sample_count"),
        },
    }
    save_rank_guard_snapshot(body)
    if not result.passed:
        try:
            from app.services.hermes.alert_dispatcher import notify_rank_guard
            notify_rank_guard(body)
        except Exception as exc:
            logger.warning("rank guard alert skipped: %s", exc)

    return body


def save_rank_guard_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """save_rank_guard_snapshot。

    参数说明：
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    if redis_client:
        redis_client.set(SNAPSHOT_KEY, json.dumps(payload, ensure_ascii=False), ex=SNAPSHOT_TTL)
    return payload


def load_rank_guard_snapshot() -> dict[str, Any] | None:
    """load_rank_guard_snapshot。
    :return: 返回处理结果。
    """
    if not redis_client:
        return None
    try:
        raw = redis_client.get(SNAPSHOT_KEY)
    except Exception:
        return None
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None
