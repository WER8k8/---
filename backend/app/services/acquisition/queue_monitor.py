# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""E-1 队列拆分监控（outreach / content / ops / default）。

原则：
    · 只读统计 ai_tasks.task_type 前缀与状态
    · 无库诚实空；不假装队列深度精确到 Celery broker
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

# task_type 前缀 → 逻辑队列
QUEUE_MAP = {
    "hermes_node:outreach": "outreach",
    "outreach": "outreach",
    "email": "outreach",
    "content": "content",
    "publish": "content",
    "site": "content",
    "hermes_node:inquiry": "ops",
    "hermes_node:order": "ops",
    "hermes_node:pi": "ops",
    "hermes_node:logistics": "ops",
    "hermes_node:billing": "ops",
    "ops": "ops",
}


def _queue_of(task_type: str) -> str:
    t = (task_type or "").lower()
    if not t:
        return "default"
    for prefix, q in QUEUE_MAP.items():
        if t.startswith(prefix) or prefix in t:
            return q
    if "dispatch" in t or "acquisition" in t:
        return "ops"
    return "default"


def queue_monitor_report(db: Any, *, tenant_id: str = "", limit: int = 500) -> dict[str, Any]:
    if db is None or not hasattr(db, "query"):
        return {
            "ok": False,
            "code": "db_unavailable",
            "queues": {},
            "plain_summary": "无数据库，无法读队列任务（诚实空）。",
        }
    try:
        from sqlalchemy import text
        from app.services.acquisition.repo import resolve_tenant_uuid

        sql = "select coalesce(task_type,'') task_type, coalesce(status,'') status, tenant_id::text tenant_id from ai_tasks"
        params: dict[str, Any] = {}
        tid = None
        if tenant_id:
            tid = resolve_tenant_uuid(db, tenant_id) or tenant_id
            sql += " where tenant_id = :tid"
            params["tid"] = tid
        sql += " order by created_at desc nulls last limit :lim"
        params["lim"] = max(1, min(5000, limit))
        rows = db.execute(text(sql), params).all()
        by_q: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "status": defaultdict(int), "types": defaultdict(int)})
        for r in rows:
            tt = str(getattr(r, "task_type", r[0] if not hasattr(r, "task_type") else "") or "")
            st = str(getattr(r, "status", r[1] if not hasattr(r, "status") else "") or "")
            q = _queue_of(tt)
            by_q[q]["total"] += 1
            by_q[q]["status"][st] += 1
            by_q[q]["types"][tt] += 1
        out = {}
        for q, agg in by_q.items():
            status = dict(agg["status"])
            failed = status.get("failed", 0) + status.get("timeout", 0)
            wait_h = status.get("wait_human", 0)
            out[q] = {
                "queue": q,
                "total": agg["total"],
                "status": status,
                "failed_or_timeout": failed,
                "wait_human": wait_h,
                "top_types": sorted(agg["types"].items(), key=lambda x: -x[1])[:5],
            }
        total = sum(v["total"] for v in out.values())
        plain = (
            f"近 {total} 条任务按队列："
            + "；".join(f"{q} {v['total']}" for q, v in sorted(out.items(), key=lambda x: -x[1]["total"]))
            if out
            else "暂无任务记录。"
        )
        return {
            "ok": True,
            "code": "ok",
            "tenant_id": tenant_id,
            "tenant_uuid": tid,
            "sampled": len(rows),
            "queues": out,
            "plain_summary": plain,
            "hint": "监控基于 ai_tasks 样本；Celery broker 队列深度需 ops 工具另查。",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "code": "error",
            "error": str(exc)[:200],
            "queues": {},
            "plain_summary": f"队列监控读取失败：{str(exc)[:120]}",
        }
