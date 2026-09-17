# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Agent run 持久化与查询。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.growth_tools import GrowthAgentRun
from app.services.agent_loop.session_store import load_run


def calc_run_progress(run: dict[str, Any]) -> int:
    """实现 计算执行progress 的功能。
    
    :param run: 参数 run（类型: dict[str, Any]）
    :return: 返回 int 结果
    """
    tasks = run.get("tasks") or []
    if not tasks:
        return 0
    done = sum(1 for t in tasks if t.get("status") in ("completed", "failed", "skipped"))
    return min(100, int(round(done / len(tasks) * 100)))


def _parse_dt(value: str | None) -> datetime | None:
    """实现 解析dt 的功能。
    
    :param value: 参数 value（类型: str | None）
    :return: 返回 datetime | None 结果
    """
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def upsert_run(db: Session, run: dict[str, Any]) -> None:
    """实现 upsert执行 的功能。
    
    :param db: 参数 db（类型: Session）
    :param run: 参数 run（类型: dict[str, Any]）
    :return: 返回 None 结果
    """
    run_id = run["id"]
    progress = calc_run_progress(run)
    run["progress"] = progress
    payload = json.dumps(run, ensure_ascii=False)
    row = db.query(GrowthAgentRun).filter(GrowthAgentRun.id == run_id).first()
    if row is None:
        row = GrowthAgentRun(
            id=run_id,
            tenant_id=run.get("tenant_id"),
            user_id=run.get("user_id"),
            workflow=run.get("workflow") or "growth_autopilot",
            goal=run.get("goal") or "",
            status=run.get("status") or "pending",
            progress=progress,
            payload=payload,
            finished_at=_parse_dt(run.get("finished_at")),
        )
        db.add(row)
    else:
        row.status = run.get("status") or row.status
        row.progress = progress
        row.payload = payload
        row.goal = run.get("goal") or row.goal
        row.finished_at = _parse_dt(run.get("finished_at")) or row.finished_at
        row.updated_at = datetime.now(timezone.utc)
    db.commit()


def sync_run(db: Session, run_id: str) -> None:
    """实现 同步执行 的功能。
    
    :param db: 参数 db（类型: Session）
    :param run_id: 参数 run_id（类型: str）
    :return: 返回 None 结果
    """
    run = load_run(run_id)
    if run:
        upsert_run(db, run)


def load_run_from_db(db: Session, run_id: str) -> dict[str, Any] | None:
    """实现 加载执行from数据库 的功能。
    
    :param db: 参数 db（类型: Session）
    :param run_id: 参数 run_id（类型: str）
    :return: 返回 dict[str, Any] | None 结果
    """
    row = db.query(GrowthAgentRun).filter(GrowthAgentRun.id == run_id).first()
    if not row or not row.payload:
        return None
    try:
        return json.loads(row.payload)
    except json.JSONDecodeError:
        return None


def get_run(db: Session, run_id: str) -> dict[str, Any] | None:
    """实现 获取执行 的功能。
    
    :param db: 参数 db（类型: Session）
    :param run_id: 参数 run_id（类型: str）
    :return: 返回 dict[str, Any] | None 结果
    """
    run = load_run(run_id)
    if run:
        return run
    return load_run_from_db(db, run_id)


def list_runs(
    db: Session,
    *,
    tenant_id: str | None = None,
    user_id: str | None = None,
    limit: int = 15,
) -> list[dict[str, Any]]:
    """实现 列出runs 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param user_id: 参数 user_id（类型: str | None）
    :param limit: 参数 limit（类型: int）
    :return: 返回 list[dict[str, Any]] 结果
    """
    q = db.query(GrowthAgentRun).order_by(GrowthAgentRun.created_at.desc())
    if tenant_id:
        q = q.filter(GrowthAgentRun.tenant_id == tenant_id)
    if user_id:
        q = q.filter(GrowthAgentRun.user_id == user_id)
    rows = q.limit(max(1, min(limit, 50))).all()
    out: list[dict[str, Any]] = []
    for row in rows:
        if not row.payload:
            continue
        try:
            run = json.loads(row.payload)
        except json.JSONDecodeError:
            continue
        out.append(
            {
                "id": row.id,
                "goal": row.goal,
                "status": row.status,
                "progress": row.progress,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "finished_at": row.finished_at.isoformat() if row.finished_at else None,
                "focus_keyword": (run.get("artifacts") or {}).get("focus_keyword", {}).get("keyword"),
                "quality_grade": (run.get("artifacts") or {}).get("inspect_report", {}).get("grade"),
            }
        )
    return out


def latest_run_summary(db: Session, *, tenant_id: str | None = None) -> dict[str, Any] | None:
    """实现 latest执行summary 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :return: 返回 dict[str, Any] | None 结果
    """
    items = list_runs(db, tenant_id=tenant_id, limit=1)
    return items[0] if items else None
