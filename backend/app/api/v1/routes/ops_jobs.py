# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""运维定时任务与作业调度路由（只读投影，写操作见 /ops-scheduler-tasks）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import get_current_user
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
