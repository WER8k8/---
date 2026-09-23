# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
# DEPRECATED (P1-14): v2ray product is legacy. Kept for backward compat; scheduled for removal after product decision.
"""V2Ray 订阅 / 节点 / 路由管理 API — 与前端 v2rayAPI 对齐。"""

from __future__ import annotations

import datetime
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.models.user import User
from app.services.admin_kv_store import (
    load_items,
    log_admin_write,
    new_id,
    now_iso,
    save_items,
)

router = APIRouter(tags=["V2Ray订阅"])

_subscriptions: list[dict[str, Any]] = []
_next_id = 1

_SERVERS_KEY = "admin_v2ray_servers"
_ROUTING_KEY = "admin_v2ray_routing"


class SubscriptionCreate(BaseModel):
    name: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    auto_update: bool = True


class V2rayServerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1, max_length=500)
    uuid: str = Field(default="", max_length=100)
    remarks: str = ""
    port: Optional[int] = None
    protocol: str = "vmess"


class V2rayServerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    uuid: Optional[str] = Field(None, max_length=100)
    remarks: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None


class V2rayRoutingCreate(BaseModel):
    rule: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=500)
    enabled: bool = True
    action: Literal["proxy", "direct", "block"] = "proxy"


class V2rayRoutingUpdate(BaseModel):
    rule: Optional[str] = Field(None, min_length=1, max_length=100)
    value: Optional[str] = Field(None, min_length=1, max_length=500)
    enabled: Optional[bool] = None
    action: Optional[Literal["proxy", "direct", "block"]] = None


def _fmt_now() -> str:
    """_fmt_now。
    :return: 返回处理结果。
    """
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")


@router.get("/subscriptions")
async def list_subscriptions(current_user: User = Depends(get_current_super_admin)):
    """list_subscriptions。

    参数说明：
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    return {"code": 0, "data": {"subscriptions": list(_subscriptions)}}


@router.post("/subscriptions")
async def create_subscription(
    body: SubscriptionCreate,
    current_user: User = Depends(get_current_super_admin),
):
    """create_subscription。

    参数说明：
    :param body: 参数 body
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    global _next_id
    item = {
        "id": _next_id,
        "name": body.name.strip(),
        "url": body.url.strip(),
        "nodes": 0,
        "s": "active",
        "updated": _fmt_now(),
        "auto_update": body.auto_update,
    }
    _next_id += 1
    _subscriptions.insert(0, item)
    return {"code": 0, "data": item, "message": "订阅已添加"}


@router.post("/subscriptions/{sub_id}/refresh")
async def refresh_subscription(
    sub_id: int,
    current_user: User = Depends(get_current_super_admin),
):
    """refresh_subscription。

    参数说明：
    :param sub_id: 参数 sub_id
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    for item in _subscriptions:
        if item["id"] == sub_id:
            item["updated"] = _fmt_now()
            return {"code": 0, "data": item, "message": "已更新"}
    raise HTTPException(status_code=404, detail="订阅不存在")


@router.delete("/subscriptions/{sub_id}")
async def delete_subscription(
    sub_id: int,
    current_user: User = Depends(get_current_super_admin),
):
    """delete_subscription。

    参数说明：
    :param sub_id: 参数 sub_id
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    global _subscriptions
    before = len(_subscriptions)
    _subscriptions = [s for s in _subscriptions if s["id"] != sub_id]
    if len(_subscriptions) == before:
        raise HTTPException(status_code=404, detail="订阅不存在")
    return {"code": 0, "message": "已删除"}


@router.get("/routing")
def list_routing_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """V2Ray 路由规则列表（SystemConfig JSON 真存储）。"""
    items = load_items(db, _ROUTING_KEY)
    return {"code": 0, "data": {"items": items, "total": len(items)}}


@router.post("/routing")
def create_routing_rule(
    body: V2rayRoutingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    items = load_items(db, _ROUTING_KEY)
    now = now_iso()
    item = {
        "id": new_id(),
        "rule": body.rule.strip(),
        "value": body.value.strip(),
        "enabled": bool(body.enabled),
        "action": body.action,
        "created_at": now,
        "updated_at": now,
    }
    items.insert(0, item)
    save_items(db, _ROUTING_KEY, items, "v2ray routing rules")
    log_admin_write(
        db,
        admin=current_user,
        action="CREATE",
        resource_type="v2ray_routing",
        resource_id=item["id"],
        detail={"rule": item["rule"], "value": item["value"], "action": item["action"]},
    )
    return {"code": 0, "data": item, "message": "规则已添加"}


@router.put("/routing/{rule_id}")
def update_routing_rule(
    rule_id: str,
    body: V2rayRoutingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    items = load_items(db, _ROUTING_KEY)
    item = next((x for x in items if x.get("id") == rule_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="规则不存在")
    if body.rule is not None:
        item["rule"] = body.rule.strip()
    if body.value is not None:
        item["value"] = body.value.strip()
    if body.enabled is not None:
        item["enabled"] = bool(body.enabled)
    if body.action is not None:
        item["action"] = body.action
    item["updated_at"] = now_iso()
    save_items(db, _ROUTING_KEY, items, "v2ray routing rules")
    log_admin_write(
        db,
        admin=current_user,
        action="UPDATE",
        resource_type="v2ray_routing",
        resource_id=rule_id,
        detail={"enabled": item.get("enabled"), "action": item.get("action")},
    )
    return {"code": 0, "data": item, "message": "规则已更新"}


@router.delete("/routing/{rule_id}")
def delete_routing_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    items = load_items(db, _ROUTING_KEY)
    before = len(items)
    items = [x for x in items if x.get("id") != rule_id]
    if len(items) == before:
        raise HTTPException(status_code=404, detail="规则不存在")
    save_items(db, _ROUTING_KEY, items, "v2ray routing rules")
    log_admin_write(
        db,
        admin=current_user,
        action="DELETE",
        resource_type="v2ray_routing",
        resource_id=rule_id,
    )
    return {"code": 0, "message": "已删除"}


@router.get("/servers")
def list_v2ray_servers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """V2Ray 节点服务器列表（SystemConfig JSON 真存储；延迟/流量不编造）。"""
    items = load_items(db, _SERVERS_KEY)
    return {"code": 0, "data": {"items": items, "total": len(items)}}


@router.post("/servers")
def create_v2ray_server(
    body: V2rayServerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    items = load_items(db, _SERVERS_KEY)
    now = now_iso()
    item = {
        "id": new_id(),
        "name": body.name.strip(),
        "address": body.address.strip(),
        "uuid": (body.uuid or "").strip(),
        "remarks": (body.remarks or "").strip(),
        "port": body.port,
        "protocol": (body.protocol or "vmess").strip(),
        "status": "unknown",
        "latency": None,
        "created_at": now,
        "updated_at": now,
    }
    items.insert(0, item)
    save_items(db, _SERVERS_KEY, items, "v2ray servers")
    log_admin_write(
        db,
        admin=current_user,
        action="CREATE",
        resource_type="v2ray_server",
        resource_id=item["id"],
        detail={"name": item["name"], "address": item["address"]},
    )
    return {"code": 0, "data": item, "message": "节点已添加"}


@router.put("/servers/{server_id}")
def update_v2ray_server(
    server_id: str,
    body: V2rayServerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    items = load_items(db, _SERVERS_KEY)
    item = next((x for x in items if x.get("id") == server_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="节点不存在")
    if body.name is not None:
        item["name"] = body.name.strip()
    if body.address is not None:
        item["address"] = body.address.strip()
    if body.uuid is not None:
        item["uuid"] = body.uuid.strip()
    if body.remarks is not None:
        item["remarks"] = body.remarks.strip()
    if body.port is not None:
        item["port"] = body.port
    if body.protocol is not None:
        item["protocol"] = body.protocol.strip() or "vmess"
    item["updated_at"] = now_iso()
    save_items(db, _SERVERS_KEY, items, "v2ray servers")
    log_admin_write(
        db,
        admin=current_user,
        action="UPDATE",
        resource_type="v2ray_server",
        resource_id=server_id,
        detail={"name": item.get("name")},
    )
    return {"code": 0, "data": item, "message": "节点已更新"}


@router.delete("/servers/{server_id}")
def delete_v2ray_server(
    server_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    items = load_items(db, _SERVERS_KEY)
    before = len(items)
    items = [x for x in items if x.get("id") != server_id]
    if len(items) == before:
        raise HTTPException(status_code=404, detail="节点不存在")
    save_items(db, _SERVERS_KEY, items, "v2ray servers")
    log_admin_write(
        db,
        admin=current_user,
        action="DELETE",
        resource_type="v2ray_server",
        resource_id=server_id,
    )
    return {"code": 0, "message": "已删除"}


@router.get("/servers/{server_id}/speed-test")
def speed_test_v2ray_server(
    server_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """测速：未配置探针时诚实 not_configured，禁止假延迟数字。"""
    items = load_items(db, _SERVERS_KEY)
    item = next((x for x in items if x.get("id") == server_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="节点不存在")
    return {
        "code": 0,
        "data": {
            "id": item.get("id"),
            "status": "not_configured",
            "latency_ms": None,
            "reason": "测速探针未配置，不返回编造延迟",
        },
    }
