# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客事件 → 经验环（Evolution）— best-effort，失败不断链。

事件：reply_ingest / ops_touch / ops_loss / intent_preview
成功/失败进入 evolution_task_records（若可写），供莫比乌斯反哺。
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def record_acquisition_event(
    db: Any,
    *,
    tenant_id: str = "",
    event: str,
    inquiry_id: str = "",
    success: bool = True,
    detail: str = "",
    executor_id: str = "acquisition_ops",
    duration_ms: int = 0,
) -> dict[str, Any]:
    """写入进化引擎。无 db/失败 → {recorded: False, reason}。"""
    event = (event or "").strip() or "unknown"
    task_type = f"acquisition.{event}"
    if db is None:
        return {"recorded": False, "reason": "db_unavailable", "task_type": task_type}

    # 1) 优先 EvolutionEngine
    try:
        from app.services.evolution.engine import EvolutionEngine
        eng = EvolutionEngine(db)
        rec = eng.record_task_execution(
            task_type=task_type,
            executor_type="workflow",
            executor_id=executor_id,
            success=success,
            duration_ms=duration_ms,
            cost=0.0,
            tokens_used=0,
            tenant_id=tenant_id or None,
            error_code=None if success else "acquisition_loss_or_fail",
            error_message=None if success else detail[:500],
            input_summary=inquiry_id,
            output_summary=detail[:500],
            metadata={"event": event, "inquiry_id": inquiry_id},
        )
        rid = getattr(rec, "id", None)
        return {"recorded": True, "engine": "EvolutionEngine", "id": str(rid) if rid else None,
                "task_type": task_type}
    except Exception as exc:  # noqa: BLE001
        logger.debug("EvolutionEngine 写入失败，尝试 terminal_hook: %s", exc)

    # 2) terminal_hook
    try:
        from app.services.trace.terminal_hook import record_terminal_state
        out = record_terminal_state(
            db,
            task_type=task_type,
            executor_type="workflow",
            executor_id=executor_id,
            success=success,
            tenant_id=tenant_id or None,
            duration_ms=duration_ms,
            input_summary=inquiry_id,
            output_summary=detail[:500],
            metadata={"event": event},
        )
        return {"recorded": True, "engine": "terminal_hook", "id": out.get("record_id") if isinstance(out, dict) else None,
                "task_type": task_type}
    except Exception as exc2:  # noqa: BLE001
        logger.warning("经验写入全部失败 event=%s: %s", event, exc2)
        return {"recorded": False, "reason": str(exc2)[:200], "task_type": task_type}


def record_ops_loss(db: Any, *, tenant_id: str, inquiry_id: str, reasons: list[str], note: str = "") -> dict[str, Any]:
    detail = "; ".join(reasons or []) + (f" | {note}" if note else "")
    return record_acquisition_event(
        db,
        tenant_id=tenant_id,
        event="ops_loss",
        inquiry_id=inquiry_id,
        success=False,
        detail=detail or "loss",
        executor_id="ops_card",
    )


def record_ops_win(
    db: Any,
    *,
    tenant_id: str,
    inquiry_id: str,
    amount: float = 0,
    currency: str = "USD",
    note: str = "",
    won_reasons: list[str] | None = None,
) -> dict[str, Any]:
    """P2-2 成交入经验环（Win）。"""
    parts = []
    if amount:
        parts.append(f"amount={amount}{currency or 'USD'}")
    if won_reasons:
        parts.append("reasons=" + ";".join(won_reasons))
    if note:
        parts.append(note)
    detail = " | ".join(parts) or "won"
    return record_acquisition_event(
        db,
        tenant_id=tenant_id,
        event="ops_win",
        inquiry_id=inquiry_id,
        success=True,
        detail=detail,
        executor_id="ops_card",
    )


def win_loss_summary(db: Any, *, tenant_id: str = "", cards: list[Any] | None = None) -> dict[str, Any]:
    """P2-2 Win/Loss 汇总（大白话）：成交几单、丢单几单、原因分布。"""
    from app.services.acquisition.loss_report import REASON_HINTS

    items = list(cards or [])
    won = [c for c in items if getattr(c, "stage", "") == "won"]
    lost = [c for c in items if getattr(c, "stage", "") == "lost" or getattr(c, "loss_reasons", None)]
    win_reasons: dict[str, int] = {}
    loss_reasons: dict[str, int] = {}
    for c in won:
        for r in getattr(c, "win_reasons", None) or []:
            win_reasons[r] = win_reasons.get(r, 0) + 1
    for c in lost:
        for r in getattr(c, "loss_reasons", None) or ["其他"]:
            loss_reasons[r] = loss_reasons.get(r, 0) + 1
    top_loss = max(loss_reasons.items(), key=lambda x: x[1])[0] if loss_reasons else ""
    top_win = max(win_reasons.items(), key=lambda x: x[1])[0] if win_reasons else ""
    plain = (
        f"成交 {len(won)} 单，流失 {len(lost)} 单。"
        + (f"赢在「{top_win}」。" if top_win else "")
        + (f"丢在「{top_loss}」——{REASON_HINTS.get(top_loss, '结合个案复盘')}。" if top_loss else "")
    )
    return {
        "tenant_id": tenant_id,
        "won_count": len(won),
        "lost_count": len(lost),
        "win_reasons": win_reasons,
        "loss_reasons": loss_reasons,
        "top_win_reason": top_win,
        "top_loss_reason": top_loss,
        "plain_summary": plain,
        "won_items": [
            {
                "inquiry_id": getattr(c, "inquiry_id", ""),
                "buyer_display": getattr(c, "buyer_display", ""),
                "amount": getattr(c, "won_amount", 0) or 0,
                "note": getattr(c, "won_note", ""),
            }
            for c in won
        ],
        "experience_hint": "成交与流失都会写入经验环；下次编排/话术可参考原因分布。",
    }
