# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P1-6 报价跟进节奏（cadence）— 排期落库。

问题：报价发出后「什么时候再联系」全靠销售记性，Next Action 常年空着，
      导致报价石沉大海（P1-6 缺口：跟进节奏未落库排期）。

方案：登记报价时按外贸 B2B 通用节奏自动生成排期，写入 OpsCard.next_action /
      next_action_at（经 ops_card_store.update → PG 持久化），让 SLA（P1-7）
      有明确的到期时间可判定，形成「排期 → 逾期告警」闭环。

节奏（可在 build_quote_cadence 调整）：
    T+1  确认客户收到报价、解答初步疑问
    T+3  跟进规格/数量确认，必要时推样品方案
    T+7  催单，确认订单意向
    T+V-2 有效期前 2 天最后确认，避免报价悄悄过期
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.services.acquisition.sla import _parse_ts

# (offset_days, 动作, 说明)
QUOTE_CADENCE: tuple[tuple[int, str, str], ...] = (
    (1, "确认客户已收到报价并解答初步疑问", "报价次日必打底：确认送达、问反馈"),
    (3, "跟进规格/数量确认，必要时提样品方案", "给技术细节与样品选项，推进决策"),
    (7, "催单：确认订单意向与预计下单时间", "明确时间点，避免无限期拖"),
)

_EXPIRY_REMIND_LEAD = 2  # 有效期前 N 天做最后确认


def build_quote_cadence(quote_at: str = "", valid_days: int = 14) -> list[dict[str, Any]]:
    """按报价日生成跟进节奏排期（含有效期前的最后确认）。"""
    start = _parse_ts(quote_at) if quote_at else None
    if start is None:
        return []
    days = int(valid_days) if valid_days else 14
    steps: list[dict[str, Any]] = []
    for offset, action, note in QUOTE_CADENCE:
        due = start + timedelta(days=offset)
        steps.append(
            {
                "offset_days": offset,
                "due_at": due.isoformat(),
                "action": action,
                "note": note,
            }
        )
    last = start + timedelta(days=max(days - _EXPIRY_REMIND_LEAD, 0))
    # 与最后一步同日则合并，避免同天两个动作
    if not steps or last.date() > _parse_ts(steps[-1]["due_at"]).date():  # type: ignore[union-attr]
        steps.append(
            {
                "offset_days": max(days - _EXPIRY_REMIND_LEAD, 0),
                "due_at": last.isoformat(),
                "action": "报价即将到期：最后确认并明确是否延期",
                "note": f"默认有效期 {days} 天，到期前 {_EXPIRY_REMIND_LEAD} 天必须确认",
            }
        )
    return steps


def current_cadence_step(
    card: Any,
    now: Optional[datetime] = None,
    valid_days: Optional[int] = None,
) -> Optional[dict[str, Any]]:
    """当前该做的那一步：以 last_touch_at 为基准推进节奏。

    从未联系过 → 第一步；已联系过 → 第一个 due 晚于最后联系的下一步。
    已走到最后一步之后 → 返回最后一步（持续提醒，不静默）。
    """
    quote_at = str(getattr(card, "quote_at", "") or "")
    if not quote_at:
        return None
    vd = int(valid_days or getattr(card, "quote_valid_days", 14) or 14)
    steps = build_quote_cadence(quote_at, vd)
    if not steps:
        return None
    touch = _parse_ts(str(getattr(card, "last_touch_at", "") or ""))
    now = now or datetime.now(timezone.utc)
    for s in steps:
        due = _parse_ts(s["due_at"])
        if due is None:
            continue
        if touch is None or due > touch:
            return s
    return steps[-1]


def apply_quote_cadence(
    card: Any,
    quote_at: str = "",
    valid_days: Optional[int] = None,
    force: bool = False,
) -> Any:
    """把当前节奏步骤写进卡片的 next_action / next_action_at（排期落库）。

    force=False 时若卡片已有 next_action 则不动（尊重人工安排）。
    返回卡片本身，便于链式 ops_card_store.update(card)。
    """
    step = current_cadence_step(card, valid_days=valid_days)
    if not step:
        return card
    if not force and str(getattr(card, "next_action", "") or "").strip():
        return card
    card.next_action = step["action"]
    card.next_action_at = step["due_at"]
    return card
