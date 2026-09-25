# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""运维定时任务与作业调度路由（只读投影，写操作见 /ops-scheduler-tasks）。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.admin_kv_store import load_items

ROUTE_PREFIX = "/ops-jobs"
ROUTE_TAGS = ["运维调度"]

router = APIRouter()

KEY = "admin_ops_scheduler_tasks"


@router.get("", include_in_schema=False)
@router.get("/")
def list_ops_jobs(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """获取系统运维与定时任务调度作业列表（真实已登记任务，无硬编码假作业）。"""
    rows = load_items(db, KEY)
    jobs = [
        {
            "id": r.get("id"),
            "name": r.get("name"),
            "cron": r.get("cron"),
            "status": "running" if r.get("enabled", True) else "paused",
            "type": r.get("type") or "custom",
            "description": r.get("description") or "",
            "enabled": bool(r.get("enabled", True)),
        }
        for r in rows
    ]
    return success_response(data={"items": jobs, "total": len(jobs)})


@router.post("/run-all")
def run_all_ops_jobs(
    dry_run: bool = Query(False),
    publish_limit: int = Query(30, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """运维收尾一键触发（对齐前端 /ops/jobs/run-all）。

    - dry_run=true：仅统计待执行发布任务数量，不执行（演练）。
    - dry_run=false：委托真实发布 worker 处理 pending 发布队列（上限 publish_limit）。
    不编造执行结果，返回 worker 真实统计。
    """
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "权限不足")
    from app.models.content import PublishTask
    from app.workers.publish_worker import run_process_pending_tasks

    pending = db.query(PublishTask).filter(PublishTask.status == "pending").count()
    if dry_run:
        return success_response(data={
            "dry_run": True,
            "pending_publish_tasks": pending,
            "would_process": min(pending, publish_limit),
            "publish_limit": publish_limit,
            "status": "dry_run",
            "note": "演练模式：未执行任何发布；执行请带 dry_run=false",
        })
    result = run_process_pending_tasks(db, limit=publish_limit)
    return success_response(data={
        "dry_run": False,
        "publish_limit": publish_limit,
        "processed": result.get("processed", 0),
        "success": result.get("success", 0),
        "failed": result.get("failed", 0),
        "recovered_stale": result.get("recovered_stale", 0),
        "status": "executed",
    })
