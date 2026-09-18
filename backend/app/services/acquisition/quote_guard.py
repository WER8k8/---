# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P3-2 报价有效期 / 汇率锁提示 + P3-3 交期门禁（禁止假交期）。

原则：
    · 报价过期必须提醒，不假装还有效
    · 无库存/无产能依据时禁止写「保证交期」
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.services.acquisition.sla import _parse_ts


def default_quote_validity_days() -> int:
    return 14


def quote_validity_view(
    *,
    quote_at: str = "",
    valid_days: Optional[int] = None,
    fx_locked: bool = False,
    fx_note: str = "",
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """报价有效期视图（大白话）。"""
    now = now or datetime.now(timezone.utc)
    days = int(valid_days) if valid_days else default_quote_validity_days()
    start = _parse_ts(quote_at) if quote_at else None
    if start is None:
        return {
            "status": "unset",
            "status_label": "未登记报价日",
            "quote_at": "",
            "valid_until": "",
            "days_left": None,
            "expired": False,
            "fx_locked": fx_locked,
            "fx_note": fx_note,
            "plain": "尚未登记报价日期；出正式报价时请写有效期。",
            "next_action": f"默认建议有效期 {days} 天；汇率波动大时锁定汇率并写明。",
        }
    valid_until = start + timedelta(days=days)
    expired = now >= valid_until
    days_left = (valid_until - now).days
    if expired:
        status, label = "expired", "已过期"
        plain = f"报价已于 {valid_until.date()} 过期，需重新核价/说明汇率。"
        next_action = "过期勿默认沿用旧价；重报并确认有效期与汇率条款。"
    elif days_left <= 3:
        status, label = "expiring", "即将过期"
        plain = f"报价还剩约 {days_left} 天有效（{valid_until.date()}）。"
        next_action = "提醒客户确认；必要时书面延长有效期。"
    else:
        status, label = "valid", "有效"
        plain = f"报价有效至 {valid_until.date()}（约 {days_left} 天）。"
        next_action = "跟进时附有效期，避免口头无限承诺。"
    if fx_locked:
        plain += " 已锁汇率。"
    elif expired:
        plain += " 注意汇率可能已变。"
    return {
        "status": status,
        "status_label": label,
        "quote_at": quote_at,
        "valid_until": valid_until.isoformat(),
        "days_left": days_left,
        "expired": expired,
        "fx_locked": fx_locked,
        "fx_note": fx_note,
        "valid_days": days,
        "plain": plain,
        "next_action": next_action,
    }


def leadtime_gate(
    *,
    has_inventory_evidence: bool = False,
    has_capacity_evidence: bool = False,
    promised_days: Optional[int] = None,
    note: str = "",
) -> dict[str, Any]:
    """P3-3 交期门禁：无证据禁止「保证交期」话术。"""
    promised = int(promised_days) if promised_days is not None else None
    evidence_ok = bool(has_inventory_evidence or has_capacity_evidence)
    if promised is None:
        allowed = False
        level = "blocked"
        plain = "未填交期天数：禁止口头「保证 XX 天」。"
        next_action = "先确认库存/产能/船期，再写工作日区间。"
    elif not evidence_ok:
        allowed = False
        level = "blocked"
        plain = f"拟承诺 {promised} 天，但无库存/产能依据 — 禁止对外保证交期。"
        next_action = "补库存或排产依据；话术改为「预计/工作日区间，以确认订单为准」。"
    elif promised <= 7 and not has_inventory_evidence:
        allowed = False
        level = "blocked"
        plain = f"拟承诺 {promised} 天（≤7）无现货证据 — 高风险，禁止保证。"
        next_action = "短交期必须现货或明确排产窗口。"
    else:
        allowed = True
        level = "ok"
        src = "现货" if has_inventory_evidence else "产能/排产"
        plain = f"交期 {promised} 天有{src}依据，可写「预计工作日」。"
        next_action = "仍须写清工作日与排产前提，勿写绝对保证。"
    return {
        "level": level,
        "allowed": allowed,
        "promised_days": promised,
        "has_inventory_evidence": has_inventory_evidence,
        "has_capacity_evidence": has_capacity_evidence,
        "plain": plain,
        "next_action": next_action,
        "note": note,
        "hint": "禁止假交期：无证据不得承诺绝对交期。",
    }
