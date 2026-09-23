# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""安全漏洞工单 CRUD（title/severity/description/status）。"""

from __future__ import annotations

from typing import Literal, Optional

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

ROUTE_PREFIX = "/security"
ROUTE_TAGS = ["安全漏洞"]

router = APIRouter()

KEY = "admin_security_tickets"


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    description: str = ""
    status: Literal["open", "fixed", "wontfix"] = "open"


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None
    description: Optional[str] = None
    status: Optional[Literal["open", "fixed", "wontfix"]] = None


@router.get("/tickets")
def list_tickets(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    if status:
        items = [x for x in items if x.get("status") == status]
    return success_response(data={"items": items, "total": len(items)})


@router.post("/tickets")
def create_ticket(
    body: TicketCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    now = now_iso()
    item = {
        "id": new_id(),
        "title": body.title.strip(),
        "severity": body.severity,
        "description": (body.description or "").strip(),
        "status": body.status,
        "created_at": now,
        "updated_at": now,
    }
    items.insert(0, item)
    save_items(db, KEY, items, "security vulnerability tickets")
    log_admin_write(
        db,
        admin=admin,
        action="CREATE",
        resource_type="security_ticket",
        resource_id=item["id"],
        detail={"title": item["title"], "severity": item["severity"], "status": item["status"]},
    )
    return success_response(data=item, message="工单已创建")


@router.put("/tickets/{ticket_id}")
def update_ticket(
    ticket_id: str,
    body: TicketUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    item = next((x for x in items if x.get("id") == ticket_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="工单不存在")
    if body.title is not None:
        item["title"] = body.title.strip()
    if body.severity is not None:
        item["severity"] = body.severity
    if body.description is not None:
        item["description"] = body.description.strip()
    if body.status is not None:
        item["status"] = body.status
    item["updated_at"] = now_iso()
    save_items(db, KEY, items, "security vulnerability tickets")
    log_admin_write(
        db,
        admin=admin,
        action="UPDATE",
        resource_type="security_ticket",
        resource_id=ticket_id,
        detail={"title": item.get("title"), "status": item.get("status")},
    )
    return success_response(data=item, message="工单已更新")


@router.delete("/tickets/{ticket_id}")
def delete_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    before = len(items)
    items = [x for x in items if x.get("id") != ticket_id]
    if len(items) == before:
        raise HTTPException(status_code=404, detail="工单不存在")
    save_items(db, KEY, items, "security vulnerability tickets")
    log_admin_write(
        db,
        admin=admin,
        action="DELETE",
        resource_type="security_ticket",
        resource_id=ticket_id,
    )
    return success_response(message="已删除")
