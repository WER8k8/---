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
