# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Accio A5：UBrain / 对外动作审计（不含真实 SMTP 外发本身）。"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.ubrain_commercial_os import UbrainActionAudit

_SENSITIVE = re.compile(
    r"(password|token|secret|api[_-]?key|authorization)",
    re.I,
)


def _preview(text: str, limit: int = 280) -> str:
    """_preview。

    参数说明：
    :param text: 参数 text
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    s = " ".join((text or "").split())
    if len(s) <= limit:
        return s
    return s[: limit - 1] + "…"


def _safe_meta(meta: dict[str, Any] | None) -> str:
    """_safe_meta。

    参数说明：
    :param meta: 参数 meta
    :return: 返回处理结果。
    """
    if not meta:
        return "{}"
    cleaned: dict[str, Any] = {}
    for k, v in meta.items():
        if _SENSITIVE.search(str(k)):
            continue
        if isinstance(v, (str, int, float, bool)) or v is None:
            cleaned[k] = v
        elif isinstance(v, list) and len(v) <= 20:
            cleaned[k] = v
    try:
        return json.dumps(cleaned, ensure_ascii=False)[:4000]
    except (TypeError, ValueError):
        return "{}"


def log_action(
    db: Session,
    *,
    tenant_id: str,
    action_type: str,
    user_id: Optional[str] = None,
    intent: Optional[str] = None,
    tool: Optional[str] = None,
    message: Optional[str] = None,
    needs_confirmation: bool = False,
    outcome: str = "ok",
    meta: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """log_action。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param action_type: 参数 action_type
    :param user_id: 参数 user_id
    :param intent: 参数 intent
    :param tool: 参数 tool
    :param message: 参数 message
    :param needs_confirmation: 参数 needs_confirmation
    :param outcome: 参数 outcome
    :param meta: 参数 meta
    :return: 返回处理结果。
    """
    row = UbrainActionAudit(
        tenant_id=str(tenant_id),
        user_id=str(user_id) if user_id else None,
        action_type=action_type[:40],
        intent=(intent or "")[:64] or None,
        tool=(tool or "")[:64] or None,
        message_preview=_preview(message or "") or None,
        needs_confirmation="true" if needs_confirmation else "false",
        outcome=outcome[:20],
        meta_json=_safe_meta(meta),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_audit(row)


def serialize_audit(row: UbrainActionAudit) -> dict[str, Any]:
    """serialize_audit。

    参数说明：
    :param row: 参数 row
    :return: 返回处理结果。
    """
    meta: dict[str, Any] = {}
    try:
        meta = json.loads(row.meta_json or "{}")
    except json.JSONDecodeError:
        meta = {}
    return {
        "id": str(row.id),
        "tenant_id": str(row.tenant_id),
        "user_id": str(row.user_id) if row.user_id else None,
        "action_type": row.action_type,
        "intent": row.intent,
        "tool": row.tool,
        "message_preview": row.message_preview,
        "needs_confirmation": row.needs_confirmation == "true",
        "outcome": row.outcome,
        "meta": meta,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def log_flywheel_action(
    db: Session,
    *,
    tenant_id: str,
    action_type: str,
    user_id: Optional[str] = None,
    intent: Optional[str] = None,
    message: Optional[str] = None,
    outcome: str = "ok",
    meta: Optional[dict[str, Any]] = None,
) -> dict[str, Any] | None:
    """飞轮 API / webhook 审计（A5 扩展）。"""
    try:
        return log_action(
            db,
            tenant_id=tenant_id,
            user_id=user_id,
            action_type=action_type,
            intent=intent,
            tool="commercial_os",
            message=message,
            needs_confirmation=False,
            outcome=outcome,
            meta=meta,
        )
    except Exception:
        return None


def list_action_audits(
    db: Session,
    tenant_id: str,
    *,
    limit: int = 50,
    action_type: Optional[str] = None,
) -> dict[str, Any]:
    """list_action_audits。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param limit: 参数 limit
    :param action_type: 参数 action_type
    :return: 返回处理结果。
    """
    q = db.query(UbrainActionAudit).filter(
        UbrainActionAudit.tenant_id == str(tenant_id)
    )
    if action_type:
        q = q.filter(UbrainActionAudit.action_type == action_type)
    rows = (
        q.order_by(UbrainActionAudit.created_at.desc()).limit(min(limit, 100)).all()
    )
    return {
        "items": [serialize_audit(r) for r in rows],
        "total": len(rows),
        "limit": limit,
    }


_SKILL_LABELS: dict[str, str] = {
    "find_buyers": "找客",
    "outreach_letter_pack": "开发信",
    "negotiation_draft": "谈单",
    "lead_content_pack": "内容包",
    "geo_content_matrix": "GEO矩阵",
    "geo_submit_pack": "GEO提交",
    "market_research": "市场研究",
    "weekly_lead_report": "线索周报",
    "sync_feedback": "效果回流",
}


def summarize_action_audits(
    db: Session,
    tenant_id: str,
    *,
    days: int = 7,
) -> dict[str, Any]:
    """销售教练：能力复盘摘要（按 intent 聚合）。"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(UbrainActionAudit)
        .filter(
            UbrainActionAudit.tenant_id == str(tenant_id),
            UbrainActionAudit.created_at >= since,
        )
        .all()
    )
    by_intent: Counter[str] = Counter()
    by_type: Counter[str] = Counter()
    for row in rows:
        by_type[row.action_type or "unknown"] += 1
        key = (row.intent or row.tool or "other").strip()
        by_intent[key] += 1
    skills = []
    max_count = max(by_intent.values(), default=0)
    for intent, count in by_intent.most_common(8):
        skills.append(
            {
                "intent": intent,
                "label": _SKILL_LABELS.get(intent, intent),
                "count": count,
                "pct": round(count / max_count * 100) if max_count else 0,
            }
        )
    return {
        "period_days": days,
        "total_actions": len(rows),
        "by_action_type": dict(by_type),
        "skills": skills,
    }
