# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""物流轨迹服务 —— 修正设计稿 模块8.4/8.5 / Production Gate G8。

红线：
- 物流状态只允许来自 tracking_events（真实承运商事件，(provider, external_event_id)
  幂等唯一）或人工录入（source=manual，operator+reason 审计）；
- **秩序守卫**：规范状态有先后秩序，回退事件（delivered 后又 in_transit）不落库、
  不回退 shipment 状态，仅记录忽略原因；
- 没有真实事件 → current_view 返回 tracking_unavailable —— **绝不伪造 in_transit**；
- sync_order_from_tracking（既有函数）对 demo payload 拒绝写回订单状态（本批次修复
  fetch_tracking 在 kuaidi100 失败时降级返回伪造轨迹的违规）。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.tracking import (
    CANONICAL_TRACKING_STATUSES,
    TRACKING_STATUS_RANK,
    TrackingEvent,
)
from app.models.trade_fulfillment import LogisticsShipment

logger = logging.getLogger(__name__)


class TrackingError(ValueError):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Provider 状态归一（扩展点：新 Provider 在此登记映射） ────────

_PROVIDER_STATUS_TOKENS: dict[str, tuple[str, ...]] = {
    "label_created": ("label created", "pre-registration", "label_created", "已下单", "揽件准备"),
    "picked_up": ("picked up", "picked_up", "揽收", "已揽收", "揽件"),
    "departed": ("departed", "departure", "已发出", "离开"),
    "in_transit": ("in transit", "in_transit", "运输中", "transit", "中转"),
    "arrived": ("arrived", "到达", "抵达"),
    "customs": ("customs", "清关", "海关", "customs clearance"),
    "out_for_delivery": ("out for delivery", "out_for_delivery", "派送中", "派件"),
    "delivered": ("delivered", "签收", "已签收", "妥投"),
    "exception": ("exception", "异常", "failed", "退回"),
}


def normalize_status(provider: str, raw_status: Optional[str], raw_text: str = "") -> str:
    """Provider 原始状态/描述 → 规范状态；无法识别 → unknown（不猜）。"""
    hay = f"{raw_status or ''} {raw_text or ''}".lower()
    if not hay.strip():
        return "unknown"
    if raw_status in CANONICAL_TRACKING_STATUSES:
        return raw_status
    best: tuple[int, str] = (0, "unknown")
    for canonical, tokens in _PROVIDER_STATUS_TOKENS.items():
        for tok in tokens:
            if tok in hay:
                rank = TRACKING_STATUS_RANK[canonical]
                if rank > best[0]:
                    best = (rank, canonical)
    return best[1]


# ── 事件入库（幂等 + 秩序守卫） ────────────────────────────────


def ingest_event(
    db: Session,
    shipment: LogisticsShipment,
    *,
    provider: str,
    external_event_id: str,
    raw_status: Optional[str] = None,
    raw_text: str = "",
    location: Optional[str] = None,
    event_time: Optional[datetime] = None,
    raw_payload: Optional[dict] = None,
    normalized_payload: Optional[dict] = None,
    source: str = "provider",
    operator: Optional[str] = None,
    operator_reason: Optional[str] = None,
) -> dict[str, Any]:
    """入库一条轨迹事件（幂等 + 秩序守卫 + shipment_stage 推导）。

    返回 {persisted, idempotent, ignored?, reason?, status}。
    """
    if not provider or not str(external_event_id or "").strip():
        raise TrackingError(400, "invalid_event", "provider 与 external_event_id 必填")
    canonical = normalize_status(provider, raw_status, raw_text or str(raw_status or ""))

    existing = (
        db.query(TrackingEvent)
        .filter(
            TrackingEvent.provider == provider,
            TrackingEvent.external_event_id == str(external_event_id),
        )
        .first()
    )
    if existing is not None:
        return {"persisted": False, "idempotent": True, "status": existing.status}

    # 秩序守卫：当前最高秩序（含 exception 特例：异常也记录，但不回退已 delivered）
    current_rank = 0
    last = (
        db.query(TrackingEvent)
        .filter(TrackingEvent.shipment_id == shipment.id)
        .order_by(TrackingEvent.created_at.desc())
        .first()
    )
    if last is not None:
        current_rank = TRACKING_STATUS_RANK.get(last.status, 0)
    new_rank = TRACKING_STATUS_RANK.get(canonical, 0)
    if new_rank < current_rank and canonical != "exception":
        logger.info(
            "tracking regression ignored: shipment=%s current=%s incoming=%s",
            shipment.id, _rank_name(current_rank), canonical,
        )
        return {"persisted": False, "ignored": True,
                "reason": f"regression: {_rank_name(current_rank)} → {canonical}"}

    event = TrackingEvent(
        shipment_id=str(shipment.id),
        tracking_no=shipment.tracking_no,
        tenant_id=shipment.tenant_id,
        provider=provider,
        external_event_id=str(external_event_id),
        status=canonical,
        location=location,
        event_time=event_time or _utcnow(),
        raw_payload=raw_payload or {},
        normalized_payload=normalized_payload or {"status": canonical},
        source=source,
        operator=operator,
        operator_reason=operator_reason,
    )
    db.add(event)

    # shipment_stage 子状态推导（设计稿 8.2）：仅由真实事件/带审计的人工录入驱动
    stage_map = {
        "label_created": "booking",
        "picked_up": "shipped",
        "departed": "shipped",
        "in_transit": "shipped",
        "arrived": "shipped",
        "customs": "shipped",
        "out_for_delivery": "shipped",
        "delivered": "delivered",
        "exception": "exception",
    }
    shipment.shipment_stage = stage_map.get(canonical, shipment.shipment_stage)
    if canonical == "delivered":
        shipment.delivered_at = event.event_time or _utcnow()
    db.add(shipment)
    db.commit()
    return {"persisted": True, "idempotent": False, "status": canonical}


def _rank_name(rank: int) -> str:
    for name, r in TRACKING_STATUS_RANK.items():
        if r == rank:
            return name
    return "unknown"


def manual_event(
    db: Session,
    shipment: LogisticsShipment,
    *,
    operator: str,
    reason: str,
    raw_status: str,
    location: Optional[str] = None,
) -> dict[str, Any]:
    """人工录入（设计稿 8.5：允许，但必须操作审计）。external_event_id 由审计信息派生。"""
    if not (operator or "").strip() or not (reason or "").strip():
        raise TrackingError(400, "manual_audit_required", "人工录入必须包含操作人与原因（审计要求）")
    import hashlib

    digest_src = f"manual:{operator}:{reason}:{_utcnow().isoformat()}"
    external_event_id = "manual-" + hashlib.sha256(digest_src.encode()).hexdigest()[:24]
    return ingest_event(
        db,
        shipment,
        provider="manual",
        external_event_id=external_event_id,
        raw_status=raw_status,
        raw_text=reason,
        location=location,
        source="manual",
        operator=operator,
        operator_reason=reason,
    )


# ── 视图 ─────────────────────────────────────────────────────


def current_view(db: Session, shipment: LogisticsShipment) -> dict[str, Any]:
    """对外轨迹视图。无真实事件 → tracking_unavailable（G8 红线：不伪造 in_transit）。"""
    events = (
        db.query(TrackingEvent)
        .filter(TrackingEvent.shipment_id == shipment.id)
        .all()
    )
    if not events:
        return {
            "shipment_id": str(shipment.id),
            "tracking_no": shipment.tracking_no,
            "status": "tracking_unavailable",
            "message": "暂无物流轨迹信息",
            "events": [],
        }
    # 最新 = 秩序最高（同秩序取时间最新）——墙钟不可靠（承运商回传乱序）
    latest = max(events, key=lambda e: (TRACKING_STATUS_RANK.get(e.status, 0), e.event_time or _utcnow().replace(tzinfo=None)))
    ordered = sorted(events, key=lambda e: (TRACKING_STATUS_RANK.get(e.status, 0), e.event_time or _utcnow().replace(tzinfo=None)), reverse=True)
    return {
        "shipment_id": str(shipment.id),
        "tracking_no": shipment.tracking_no,
        "status": latest.status,
        "shipment_stage": shipment.shipment_stage,
        "events": [
            {
                "status": e.status,
                "location": e.location,
                "event_time": e.event_time.isoformat() if e.event_time else None,
                "provider": e.provider,
                "source": e.source,
            }
            for e in ordered
        ],
    }
