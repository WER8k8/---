# DEPRECATED (P1-14): v2ray product is legacy. Kept for backward compat; scheduled for removal after product decision.
"""V2Ray 订阅管理 API — 与前端 v2rayAPI / subscription.vue 对齐。"""

from __future__ import annotations

import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.admin_auth import get_current_super_admin
from app.models.user import User

router = APIRouter(tags=["V2Ray订阅"])

_subscriptions: list[dict[str, Any]] = []
_next_id = 1


class SubscriptionCreate(BaseModel):
    name: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    auto_update: bool = True


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
async def list_routing_rules(current_user: User = Depends(get_current_super_admin)):
    """V2Ray 路由规则列表"""
    return {"code": 0, "data": {"items": [], "total": 0}}


@router.get("/servers")
async def list_v2ray_servers(current_user: User = Depends(get_current_super_admin)):
    """V2Ray 节点服务器列表"""
    return {"code": 0, "data": {"items": [], "total": 0}}
