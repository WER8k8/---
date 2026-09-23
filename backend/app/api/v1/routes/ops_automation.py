# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""运维自动化 CRUD：workflow / script / schedule_slot（SystemConfig JSON）。"""

from __future__ import annotations

from typing import Any, Literal, Optional

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

ROUTE_PREFIX = "/ops-automations"
ROUTE_TAGS = ["运维自动化"]

router = APIRouter()

KEY = "admin_ops_automations"
KINDS = ("workflow", "script", "schedule_slot")


class AutomationCreate(BaseModel):
    kind: Literal["workflow", "script", "schedule_slot"]
    name: str = Field(..., min_length=1, max_length=200)
    steps: Optional[str] = None
    body: Optional[str] = None
    cron: Optional[str] = None
    payload: Optional[dict[str, Any]] = None


class AutomationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    steps: Optional[str] = None
    body: Optional[str] = None
    cron: Optional[str] = None
    payload: Optional[dict[str, Any]] = None


def _require_kind_fields(kind: str, *, steps: Optional[str], body: Optional[str], cron: Optional[str]) -> None:
    if kind == "workflow" and not (steps or "").strip():
        raise HTTPException(status_code=422, detail="workflow 需要 steps")
    if kind == "script" and not (body or "").strip():
        raise HTTPException(status_code=422, detail="script 需要 body")
    if kind == "schedule_slot" and not (cron or "").strip():
        raise HTTPException(status_code=422, detail="schedule_slot 需要 cron")


@router.get("")
@router.get("/")
def list_automations(
    kind: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    if kind:
        if kind not in KINDS:
            raise HTTPException(status_code=422, detail=f"kind 必须是 {KINDS}")
        items = [x for x in items if x.get("kind") == kind]
    return success_response(data={"items": items, "total": len(items)})


@router.post("")
@router.post("/")
def create_automation(
    body: AutomationCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    _require_kind_fields(body.kind, steps=body.steps, body=body.body, cron=body.cron)
    items = load_items(db, KEY)
    now = now_iso()
    item = {
        "id": new_id(),
        "kind": body.kind,
        "name": body.name.strip(),
        "steps": (body.steps or "").strip() or None,
        "body": (body.body or "").strip() or None,
        "cron": (body.cron or "").strip() or None,
        "payload": body.payload or {},
        "created_at": now,
        "updated_at": now,
    }
    items.insert(0, item)
    save_items(db, KEY, items, "ops automations workflow/script/schedule_slot")
    log_admin_write(
        db,
        admin=admin,
        action="CREATE",
        resource_type="ops_automation",
        resource_id=item["id"],
        detail={"kind": body.kind, "name": item["name"]},
    )
    return success_response(data=item, message="已创建")


@router.put("/{item_id}")
def update_automation(
    item_id: str,
    body: AutomationUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    item = next((x for x in items if x.get("id") == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="记录不存在")
    if body.name is not None:
        item["name"] = body.name.strip()
    if body.steps is not None:
        item["steps"] = body.steps.strip() or None
    if body.body is not None:
        item["body"] = body.body.strip() or None
    if body.cron is not None:
        item["cron"] = body.cron.strip() or None
    if body.payload is not None:
        item["payload"] = body.payload
    kind = item.get("kind") or "workflow"
    _require_kind_fields(kind, steps=item.get("steps"), body=item.get("body"), cron=item.get("cron"))
    item["updated_at"] = now_iso()
    save_items(db, KEY, items, "ops automations workflow/script/schedule_slot")
    log_admin_write(
        db,
        admin=admin,
        action="UPDATE",
        resource_type="ops_automation",
        resource_id=item_id,
        detail={"name": item.get("name"), "kind": kind},
    )
    return success_response(data=item, message="已更新")


@router.delete("/{item_id}")
def delete_automation(
    item_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    before = len(items)
    items = [x for x in items if x.get("id") != item_id]
    if len(items) == before:
        raise HTTPException(status_code=404, detail="记录不存在")
    save_items(db, KEY, items, "ops automations workflow/script/schedule_slot")
    log_admin_write(
        db,
        admin=admin,
        action="DELETE",
        resource_type="ops_automation",
        resource_id=item_id,
    )
    return success_response(message="已删除")
