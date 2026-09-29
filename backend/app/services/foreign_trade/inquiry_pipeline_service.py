# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GW-L-PL-01 — 询盘管道阶段 MQL→SQL→报价→PI→定金。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry
from app.services.billing.reservation_service import IllegalTransition
from app.services.foreign_trade.inquiry_meddpicc_service import load_meddpicc, save_meddpicc
from app.services.inquiry_status_service import advance_inquiry_status

logger = logging.getLogger(__name__)

PIPELINE_STAGES: tuple[dict[str, str], ...] = (
    {"id": "mql", "label": "MQL", "label_zh": "营销合格线索"},
    {"id": "sql", "label": "SQL", "label_zh": "销售合格线索"},
    {"id": "quote", "label": "Quote", "label_zh": "报价"},
    {"id": "pi", "label": "PI", "label_zh": "形式发票"},
    {"id": "deposit", "label": "Deposit", "label_zh": "定金"},
)

STAGE_IDS = frozenset(s["id"] for s in PIPELINE_STAGES)

_STATUS_TO_STAGE = {
    "pending": "mql",
    "quoted": "quote",
    "closed": "deposit",
    "lost": "mql",
}


def _utcnow_iso() -> str:
    """实现 utcnowiso 的功能。
    
    :return: 返回 str 结果
    """
    return datetime.now(timezone.utc).isoformat()


def _advance_status_best_effort(
    db: Session,
    inquiry: Inquiry,
    new_status: str,
    *,
    source: str,
    actor_id: Optional[str] = None,
) -> None:
    """经唯一汇聚点推进询盘状态；非法跃迁记结构化日志但不阻断管道阶段落库。

    管道阶段（meddpicc meta）已先落库，状态推进属附带语义；此处绝不直写
    inquiries.status（模块10 收敛），但也不因状态守卫拒绝而抛错打挂主链。
    """
    try:
        advance_inquiry_status(db, inquiry, new_status, source=source, actor_id=actor_id)
    except (ValueError, IllegalTransition) as exc:
        logger.warning(
            "管道推进询盘状态被拒（不阻断阶段落库）：inquiry_id=%s target=%s reason=%s",
            getattr(inquiry, "id", None), new_status, exc,
        )


def get_pipeline_stage(inquiry: Inquiry) -> str:
    """实现 获取pipelinestage 的功能。
    
    :param inquiry: 参数 inquiry（类型: Inquiry）
    :return: 返回 str 结果
    """
    meta = load_meddpicc(inquiry)
    stage = str(meta.get("pipeline_stage") or "").strip().lower()
    if stage in STAGE_IDS:
        return stage
    return _STATUS_TO_STAGE.get(str(inquiry.status or "").lower(), "mql")


def pipeline_stage_meta(inquiry: Inquiry) -> dict[str, Any]:
    """实现 pipelinestagemeta 的功能。
    
    :param inquiry: 参数 inquiry（类型: Inquiry）
    :return: 返回 dict[str, Any] 结果
    """
    meta = load_meddpicc(inquiry)
    stage = get_pipeline_stage(inquiry)
    history = meta.get("pipeline_history")
    if not isinstance(history, list):
        history = []
    label = next((s["label_zh"] for s in PIPELINE_STAGES if s["id"] == stage), stage)
    return {
        "pipeline_stage": stage,
        "pipeline_stage_label": label,
        "pipeline_history": history[-10:],
        "gw_task": "GW-L-PL-01",
    }


def set_pipeline_stage(
    db: Session,
    inquiry: Inquiry,
    *,
    stage: str,
    user_id: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """实现 设置pipelinestage 的功能。
    
    :param db: 参数 db（类型: Session）
    :param inquiry: 参数 inquiry（类型: Inquiry）
    :param stage: 参数 stage（类型: str）
    :param user_id: 参数 user_id（类型: str | None）
    :param note: 参数 note（类型: str | None）
    :return: 返回 dict[str, Any] 结果
    :raises ValueError: 当操作失败时抛出 ValueError 异常
    """
    normalized = (stage or "").strip().lower()
    if normalized not in STAGE_IDS:
        raise ValueError(f"invalid pipeline_stage: {stage}")

    meta = load_meddpicc(inquiry)
    prev = get_pipeline_stage(inquiry)
    history = meta.get("pipeline_history")
    if not isinstance(history, list):
        history = []
    history.append(
        {
            "from": prev,
            "to": normalized,
            "at": _utcnow_iso(),
            "by": user_id,
            "note": (note or "")[:300] or None,
        }
    )
    meta["pipeline_stage"] = normalized
    meta["pipeline_history"] = history[-30:]
    save_meddpicc(db, inquiry, meta)
    if normalized in {"quote", "pi", "deposit"} and inquiry.status == "pending":
        # 模块10 收敛：经唯一汇聚点推进（禁止直写；含白名单/漏斗守卫/计费时点）
        _advance_status_best_effort(
            db, inquiry, "quoted", source="pipeline_quote", actor_id=user_id)
    if normalized == "deposit":
        _advance_status_best_effort(
            db, inquiry, "closed", source="pipeline_deposit", actor_id=user_id)

    return pipeline_stage_meta(inquiry)


def pipeline_summary(
    db: Session,
    *,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """实现 pipelinesummary 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :return: 返回 dict[str, Any] 结果
    """
    q = db.query(Inquiry)
    cols = {c.key for c in Inquiry.__table__.columns}
    if "is_active" in cols:
        q = q.filter(Inquiry.is_active.is_(True))
    if tenant_id and "tenant_id" in cols:
        q = q.filter(Inquiry.tenant_id == tenant_id)

    counts = {s["id"]: 0 for s in PIPELINE_STAGES}
    rows = q.order_by(Inquiry.created_at.desc()).limit(500).all()
    for row in rows:
        counts[get_pipeline_stage(row)] = counts.get(get_pipeline_stage(row), 0) + 1

    return {
        "stages": list(PIPELINE_STAGES),
        "counts": counts,
        "total": sum(counts.values()),
        "gw_task": "GW-L-PL-01",
    }


def enrich_inquiry_pipeline_fields(item: dict[str, Any], inquiry: Inquiry | None = None) -> dict[str, Any]:
    """实现 enrichinquirypipeline字段 的功能。
    
    :param item: 参数 item（类型: dict[str, Any]）
    :param inquiry: 参数 inquiry（类型: Inquiry | None）
    :return: 返回 dict[str, Any] 结果
    """
    if inquiry is not None:
        meta = pipeline_stage_meta(inquiry)
    else:
        med = item.get("meddpicc") if isinstance(item.get("meddpicc"), dict) else {}
        stage = str(med.get("pipeline_stage") or _STATUS_TO_STAGE.get(str(item.get("status") or ""), "mql"))
        label = next((s["label_zh"] for s in PIPELINE_STAGES if s["id"] == stage), stage)
        meta = {"pipeline_stage": stage, "pipeline_stage_label": label}
    return {**item, **meta}
