# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客跟进 SLA — 逾期提醒（大白话）。

规则：
    · 卡片丢失 stage=lost → 不进待办
    · 有 next_action_at：到期/逾期 → due/overdue
    · 无 next_action_at 但有 next_action：默认 last_touch+24h 估算
    · 超过 72h 无下一步且无 touch → overdue
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional


def _parse_ts(value: str) -> Optional[datetime]:
    if not value:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:  # noqa: BLE001
        return None


def evaluate_sla(
    *,
    stage: str = "",
    next_action: str = "",
    next_action_at: str = "",
    last_touch_at: str = "",
    now: Optional[datetime] = None,
    due_hours: int = 24,
    overdue_hours: int = 72,
) -> dict[str, Any]:
    """返回 {sla, due_at, overdue, display}。sla ∈ ok|due|overdue|none|closed"""
    if (stage or "").lower() == "lost":
        return {
            "sla": "closed",
            "due_at": "",
            "overdue": False,
            "display": "已流失，不进待办",
        }
    now = now or datetime.now(timezone.utc)
    due = _parse_ts(next_action_at)
    if due is None:
        touch = _parse_ts(last_touch_at)
        if touch and (next_action or "").strip():
            due = touch + timedelta(hours=due_hours)
        elif touch:
            limit = touch + timedelta(hours=overdue_hours)
            if now >= limit:
                return {
                    "sla": "overdue",
                    "due_at": "",
                    "overdue": True,
                    "display": f"已 {overdue_hours}h 无跟进，请安排联系",
                }
            return {
                "sla": "none",
                "due_at": "",
                "overdue": False,
                "display": "暂无明确下一步",
            }
        else:
            return {
                "sla": "none",
                "due_at": "",
                "overdue": False,
                "display": "尚未联系",
            }
    due_s = due.isoformat()
    if now >= due:
        hours = max(0, int((now - due).total_seconds() // 3600))
        return {
            "sla": "overdue",
            "due_at": due_s,
            "overdue": True,
            "display": f"已逾期约 {hours} 小时，优先处理",
        }
    hours_left = int((due - now).total_seconds() // 3600)
    return {
        "sla": "due",
        "due_at": due_s,
        "overdue": False,
        "display": f"请在约 {hours_left} 小时内跟进",
    }


def card_sla(card: Any, now: Optional[datetime] = None) -> dict[str, Any]:
    """从 OpsCard 计算 SLA。"""
    return evaluate_sla(
        stage=getattr(card, "stage", "") or "",
        next_action=getattr(card, "next_action", "") or "",
        next_action_at=getattr(card, "next_action_at", "") or "",
        last_touch_at=getattr(card, "last_touch_at", "") or "",
        now=now,
    )


def default_next_action_at(now: Optional[datetime] = None, hours: int = 24) -> str:
    now = now or datetime.now(timezone.utc)
    return (now + timedelta(hours=hours)).isoformat()
