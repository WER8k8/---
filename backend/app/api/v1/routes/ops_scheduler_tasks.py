# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""调度任务 CRUD：name/cron/description/enabled（SystemConfig JSON）。"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.services.admin_kv_store import (
    load_items,
    log_admin_write,
    new_id,
    now_iso,
    save_items,
)

ROUTE_PREFIX = "/ops-scheduler-tasks"
ROUTE_TAGS = ["运维调度"]

router = APIRouter()

KEY = "admin_ops_scheduler_tasks"


class SchedulerTaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    cron: str = Field(..., min_length=1, max_length=80)
    description: str = ""
    type: str = "custom"
    enabled: bool = True


class SchedulerTaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    cron: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = None
    type: Optional[str] = None
    enabled: Optional[bool] = None


class SchedulerTaskToggle(BaseModel):
    enabled: bool


@router.get("")
@router.get("/")
def list_scheduler_tasks(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    return success_response(data={"items": items, "total": len(items)})


@router.post("")
@router.post("/")
def create_scheduler_task(
    body: SchedulerTaskCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    now = now_iso()
    item = {
        "id": new_id(),
        "name": body.name.strip(),
        "cron": body.cron.strip(),
        "description": (body.description or "").strip(),
        "type": (body.type or "custom").strip() or "custom",
        "enabled": bool(body.enabled),
        "created_at": now,
        "updated_at": now,
    }
    items.insert(0, item)
    save_items(db, KEY, items, "ops scheduler tasks")
    log_admin_write(
        db,
        admin=admin,
        action="CREATE",
        resource_type="ops_scheduler_task",
        resource_id=item["id"],
        detail={"name": item["name"], "cron": item["cron"], "enabled": item["enabled"]},
    )
    return success_response(data=item, message="任务已创建")


@router.put("/{task_id}")
def update_scheduler_task(
    task_id: str,
    body: SchedulerTaskUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    item = next((x for x in items if x.get("id") == task_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="任务不存在")
    if body.name is not None:
        item["name"] = body.name.strip()
    if body.cron is not None:
        item["cron"] = body.cron.strip()
    if body.description is not None:
        item["description"] = body.description.strip()
    if body.type is not None:
        item["type"] = body.type.strip() or "custom"
    if body.enabled is not None:
        item["enabled"] = bool(body.enabled)
    item["updated_at"] = now_iso()
    save_items(db, KEY, items, "ops scheduler tasks")
    log_admin_write(
        db,
        admin=admin,
        action="UPDATE",
        resource_type="ops_scheduler_task",
        resource_id=task_id,
        detail={"name": item.get("name"), "enabled": item.get("enabled")},
    )
    return success_response(data=item, message="任务已更新")


@router.patch("/{task_id}/enabled")
def toggle_scheduler_task(
    task_id: str,
    body: SchedulerTaskToggle,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    item = next((x for x in items if x.get("id") == task_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="任务不存在")
    item["enabled"] = bool(body.enabled)
    item["updated_at"] = now_iso()
    save_items(db, KEY, items, "ops scheduler tasks")
    log_admin_write(
        db,
        admin=admin,
        action="TOGGLE",
        resource_type="ops_scheduler_task",
        resource_id=task_id,
        detail={"enabled": item["enabled"]},
    )
    return success_response(data=item, message="已启用" if item["enabled"] else "已停用")


@router.delete("/{task_id}")
def delete_scheduler_task(
    task_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    before = len(items)
    items = [x for x in items if x.get("id") != task_id]
    if len(items) == before:
        raise HTTPException(status_code=404, detail="任务不存在")
    save_items(db, KEY, items, "ops scheduler tasks")
    log_admin_write(
        db,
        admin=admin,
        action="DELETE",
        resource_type="ops_scheduler_task",
        resource_id=task_id,
    )
    return success_response(message="已删除")
