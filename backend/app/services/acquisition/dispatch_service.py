# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客一键派发：复用 planner + 爱马仕 supervisor，诚实返回。"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _as_session(db: Any) -> Any:
    if db is None:
        return None
    if type(db).__name__ in ("Depends",):
        return None
    if not hasattr(db, "add"):
        return None
    return db


async def dispatch_acquisition(
    db: Any,
    *,
    tenant_id: str,
    intent: str,
    payload: Optional[dict[str, Any]] = None,
    channel: str = "acquisition_ops",
    auto_dispatch: bool = False,
) -> dict[str, Any]:
    """意图拆解 →（可选）任务图落库派发。

    返回 dict；失败抛 HTTP 友好异常信息由路由包装。
    """
    session = _as_session(db)
    payload = dict(payload or {})
    event_id = f"acq_{uuid.uuid4().hex[:12]}"
    from app.schemas.hermes_orchestration import IntentEvent
    from app.services.hermes import planner_service as ps

    event = IntentEvent(
        event_id=event_id,
        tenant_id=tenant_id or "unknown",
        channel=channel,
        intent=intent,
        payload=payload,
    )
    graph, source = await ps.decompose(event, session)
    nodes = [
        {
            "id": n.id,
            "executor": n.executor,
            "capability": n.capability,
            "depends_on": list(n.depends_on or []),
        }
        for n in graph.nodes
    ]
    result: dict[str, Any] = {
        "plan_id": graph.plan_id,
        "graph_source": source,
        "node_count": len(graph.nodes),
        "nodes": nodes,
        "approval_required": list(graph.policies.approval_required or []),
        "dispatched": False,
        "task_ids": [],
        "plan_task_id": "",
        "dispatch_error": "",
        "persistence_note": "",
    }
    if not auto_dispatch:
        result["persistence_note"] = "仅拆解预览，未派发（auto_dispatch=false）"
        return result
    if session is None:
        result["dispatch_error"] = "db_unavailable"
        result["persistence_note"] = "无数据库会话，跳过任务落库/派发（诚实失败）"
        return result
    try:
        from app.services.hermes.task_control_supervisor import (
            advance_plan,
            parse_graph_to_tasks,
        )
        node_tasks = parse_graph_to_tasks(session, tenant_id, graph)
        plan_task_id = str(getattr(node_tasks[0], "parent_task_id", "")) if node_tasks else ""
        result["task_ids"] = [str(getattr(t, "id", "")) for t in node_tasks]
        result["plan_task_id"] = plan_task_id
        if plan_task_id:
            try:
                advance_plan(session, plan_task_id)
                result["dispatched"] = True
                result["persistence_note"] = f"任务图已入库 plan={plan_task_id}"
            except Exception as exc:  # noqa: BLE001
                result["dispatch_error"] = str(exc)[:200]
                result["persistence_note"] = "任务图已入库，派发失败（诚实）"
        else:
            result["dispatch_error"] = "no_plan_task_id"
            result["persistence_note"] = "落库未返回 plan_task_id"
    except Exception as exc:  # noqa: BLE001
        logger.exception("dispatch_acquisition 落库失败")
        result["dispatch_error"] = str(exc)[:200]
        result["persistence_note"] = "任务图落库失败"
    return result
