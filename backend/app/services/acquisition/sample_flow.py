# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""样品 Sample 状态机（P1-5）— 寄样可追踪，费用不黑洞。

状态：
    none → requested → confirmed → preparing → shipped → delivered
    费用：unbilled → billed → paid / waived
    取消：rejected
"""
from __future__ import annotations

from typing import Any

SAMPLE_STATUSES = (
    "none",
    "requested",
    "confirmed",
    "preparing",
    "shipped",
    "delivered",
    "fee_collected",
    "waived",
    "rejected",
)

STATUS_LABELS = {
    "none": "未启动",
    "requested": "客户要样品",
    "confirmed": "规格/费用已确认",
    "preparing": "备样中",
    "shipped": "已寄出",
    "delivered": "已签收",
    "fee_collected": "样品费已收",
    "waived": "免费寄样",
    "rejected": "已取消",
}

# 允许的合法流转（从 → 可到）
_TRANSITIONS: dict[str, set[str]] = {
    "none": {"requested", "rejected"},
    "requested": {"confirmed", "waived", "rejected"},
    "confirmed": {"preparing", "waived", "rejected"},
    "preparing": {"shipped", "rejected"},
    "shipped": {"delivered", "fee_collected", "rejected"},
    "delivered": {"fee_collected", "waived"},
    "fee_collected": set(),
    "waived": set(),
    "rejected": set(),
}

NEXT_ACTIONS = {
    "none": "客户提样品时点「客户要样品」",
    "requested": "确认样品规格、费用谁出、快递到付/寄付",
    "confirmed": "安排备样，拍照留档",
    "preparing": "备好后登记快递单号并寄出",
    "shipped": "跟快递签收；到期催确认",
    "delivered": "确认收到后谈费用或推进大货",
    "fee_collected": "样品闭环，推进大货报价/PI",
    "waived": "免费样已登记，继续跟进大货",
    "rejected": "样品取消，原因写进备注",
}


def can_transition(from_status: str, to_status: str) -> bool:
    if from_status == to_status:
        return True
    if to_status not in SAMPLE_STATUSES:
        return False
    return to_status in _TRANSITIONS.get(from_status, set())


def sample_view(sample: Any) -> dict[str, Any]:
    if sample is None:
        status = "none"
        payload: dict[str, Any] = {}
    else:
        status = getattr(sample, "status", None) or "none"
        payload = {
            "status": status,
            "label": STATUS_LABELS.get(status, status),
            "product": getattr(sample, "product", "") or "",
            "spec": getattr(sample, "spec", "") or "",
            "qty": getattr(sample, "qty", 0) or 0,
            "unit": getattr(sample, "unit", "") or "",
            "fee_amount": getattr(sample, "fee_amount", 0) or 0,
            "fee_currency": getattr(sample, "fee_currency", "USD") or "USD",
            "fee_status": getattr(sample, "fee_status", "unbilled") or "unbilled",
            "courier": getattr(sample, "courier", "") or "",
            "tracking_no": getattr(sample, "tracking_no", "") or "",
            "shipped_at": getattr(sample, "shipped_at", "") or "",
            "note": getattr(sample, "note", "") or "",
            "updated_at": getattr(sample, "updated_at", "") or "",
        }
    fee_hole = False
    if payload:
        if payload.get("status") in ("shipped", "delivered") and payload.get("fee_status") in (
            "unbilled",
            "billed",
        ) and (payload.get("fee_amount") or 0) > 0:
            fee_hole = True
    return {
        **payload,
        "status": status,
        "label": STATUS_LABELS.get(status, status),
        "next_action": NEXT_ACTIONS.get(status, "按流程推进寄样"),
        "allowed_next": sorted(_TRANSITIONS.get(status, set())),
        "fee_hole_risk": fee_hole,
        "hint": "样品费与运费归属要写清楚；未收齐勿默认免费。",
    }
