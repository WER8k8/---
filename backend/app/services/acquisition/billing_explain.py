# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P2-6 账单明细可解释 — Token/动作在大白话里说得清。

红线：
    · 无账本/无明细诚实 empty，不编流水
    · 只读 token_ledger + meter_events + 获客经验事件
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _reason_plain(reason: str) -> str:
    r = (reason or "").lower()
    mapping = {
        "p0_seed_grant": "联调种子充值",
        "p0_wallet_topup": "联调加币",
        "ai_generation": "AI 生成消耗",
        "grant": "套餐/充值入账",
        "recharge": "充值",
        "subscribe": "订阅扣减",
        "topup": "充值",
        "deduct": "用量扣减",
        "refund": "退款",
    }
    if reason in mapping:
        return mapping[reason]
    if "ops_dispatch" in r or "dispatch" in r:
        return "获客智能派发"
    if "ops_win" in r:
        return "成交经验入环"
    if "ops_loss" in r:
        return "流失经验入环"
    if "reply_ingest" in r:
        return "询盘进线建档"
    return reason or "未知原因"


def billing_explain(
    db: Any,
    *,
    tenant_id: str = "demo",
    limit: int = 20,
) -> dict[str, Any]:
    """每次 Token/动作的大白话账单。"""
    from app.services.acquisition.repo import resolve_tenant_uuid

    session = db
    if session is None or not hasattr(session, "query"):
        return {
            "tenant_id": tenant_id,
            "balance": None,
            "items": [],
            "plain_summary": "无数据库会话，账单无法解释（诚实空）。",
            "source": "none",
            "hint": "接 PG 后可查 token_ledger / meter_events / 获客事件。",
        }

    tid = resolve_tenant_uuid(session, tenant_id) or tenant_id
    items: list[dict[str, Any]] = []
    balance: Optional[int] = None

    try:
        from app.models.token_ledger import TokenLedgerEntry
        rows = (
            session.query(TokenLedgerEntry)
            .filter(TokenLedgerEntry.tenant_id == tid)
            .order_by(TokenLedgerEntry.created_at.desc())
            .limit(limit)
            .all()
        )
        if rows:
            balance = int(getattr(rows[0], "balance_after", 0) or 0)
        for r in rows:
            delta = int(getattr(r, "delta", 0) or 0)
            reason = str(getattr(r, "reason", "") or "")
            items.append({
                "at": str(getattr(r, "created_at", "") or ""),
                "kind": "token",
                "delta": delta,
                "balance_after": int(getattr(r, "balance_after", 0) or 0),
                "reason": reason,
                "plain": f"{'入账' if delta >= 0 else '扣减'} {abs(delta)} Token · {_reason_plain(reason)}",
                "reference_id": str(getattr(r, "reference_id", "") or ""),
            })
    except Exception as exc:  # noqa: BLE001
        logger.warning("token_ledger 解释失败: %s", exc)

    try:
        from app.models.meter import MeterEvent
        meters = (
            session.query(MeterEvent)
            .filter(MeterEvent.tenant_id == tid)
            .order_by(MeterEvent.occurred_at.desc())
            .limit(limit)
            .all()
        )
        for m in meters:
            mt = str(getattr(m, "meter_type", "") or "")
            tokens = getattr(m, "token_delta", None) or getattr(m, "tokens", None) or 0
            items.append({
                "at": str(getattr(m, "occurred_at", "") or ""),
                "kind": "meter",
                "delta": int(tokens or 0),
                "balance_after": None,
                "reason": mt,
                "plain": f"计量事件 · {mt}" + (f" · 约 {tokens} token" if tokens else ""),
                "reference_id": str(getattr(m, "source_ref_id", "") or ""),
            })
    except Exception:
        pass

    try:
        from app.models.evolution import EvolutionTaskRecord
        acq = (
            session.query(EvolutionTaskRecord)
            .filter(EvolutionTaskRecord.task_type.like("acquisition.%"))
            .order_by(EvolutionTaskRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        for r in acq:
            t = str(getattr(r, "task_type", "") or "")
            items.append({
                "at": str(getattr(r, "created_at", "") or ""),
                "kind": "acquisition",
                "delta": 0,
                "balance_after": None,
                "reason": t,
                "plain": f"获客动作 · {_reason_plain(t)} · {'成功' if getattr(r, 'success', True) else '失败/诚实降级'}",
                "reference_id": str(getattr(r, "input_summary", "") or ""),
            })
    except Exception:
        pass

    items.sort(key=lambda x: str(x.get("at") or ""), reverse=True)
    items = items[:limit]
    plain = (
        f"当前余额 {balance} Token，近 {len(items)} 条明细。"
        if balance is not None
        else f"近 {len(items)} 条明细；余额未知（无账本流水）。"
    )
    return {
        "tenant_id": tenant_id,
        "tenant_uuid": tid,
        "balance": balance,
        "items": items,
        "plain_summary": plain,
        "source": "token_ledger+meter+acquisition",
        "hint": "每次扣减/入账都带大白话原因；无流水不编造。",
    }
