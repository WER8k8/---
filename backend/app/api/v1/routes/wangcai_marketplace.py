# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""旺财插件市场 — 对外 API（不含 Hermes / 第三方商标）。"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.hermes.brand_guard import sanitize_public_data
from app.services.hermes.install_service import (
    ensure_default_plugins,
    install_plugin,
    list_tenant_installs,
    set_plugin_enabled,
)
from app.services.hermes.browser_companion import list_browser_companions
from app.services.hermes.registry import catalog_meta, list_plugins, public_market_item
from app.services.hermes.runtime import HermesPluginError, execute_plugin
from app.api.v1.routes.ubrain import _resolve_tenant_id


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/wangcai/plugins", tags=["旺财插件市场"])


@router.get("/marketplace")
def wangcai_marketplace(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category: str | None = Query(None),
):
    """旺财插件市场目录（仅 public 插件）。"""
    tenant_id = _resolve_tenant_id(current_user, db)
    if tenant_id:
        ensure_default_plugins(db, str(tenant_id), str(current_user.id) if current_user else None)

    installed = {}
    if tenant_id:
        for row in list_tenant_installs(db, str(tenant_id)):
            installed[row.plugin_id] = {"enabled": row.enabled, "version": row.plugin_version}

    items = []
    for p in list_plugins(visibility="public"):
        if category and (p.get("public") or {}).get("category") != category:
            continue
        item = public_market_item(p)
        inst = installed.get(p["id"])
        item["installed"] = inst is not None
        item["enabled"] = inst["enabled"] if inst else p["id"] in installed or False
        items.append(item)

    return success_response(
        data=sanitize_public_data(
            {
                "brand": "旺财插件市场",
                "meta": catalog_meta(),
                "items": items,
            }
        )
    )


@router.get("/browser-companions")
def wangcai_browser_companions(
    content_type: str | None = Query(None, description="video | article"),
    current_user: User = Depends(get_current_user),
):
    """本地浏览器扩展推荐（Chrome/Edge 安装，非服务端执行）。"""
    del current_user
    items = list_browser_companions(content_type=content_type)
    return success_response(
        data={
            "items": items,
            "message": "请在客户本机 Chrome/Edge 安装；与云端 Worker 真发互补。",
        }
    )


@router.get("/installed")
def wangcai_installed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /installed 请求，wangcai相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    ensure_default_plugins(db, str(tenant_id))
    rows = list_tenant_installs(db, str(tenant_id))
    items = []
    for row in rows:
        from app.services.hermes.registry import get_plugin
        spec = get_plugin(row.plugin_id)
        if not spec or spec.get("visibility") != "public":
            continue
        items.append(
            {
                **public_market_item(spec),
                "enabled": row.enabled,
                "installed_at": row.installed_at.isoformat() if row.installed_at else None,
            }
        )
    return success_response(data={"items": items})


class InstallBody(BaseModel):
    enabled: bool = True


@router.post("/{plugin_id}/install")
def wangcai_install(
    plugin_id: str,
    body: InstallBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /{plugin_id}/install 请求，wangcai相关资源。
    
    :param plugin_id: 参数 plugin_id
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    try:
        row = install_plugin(
            db,
            tenant_id=str(tenant_id),
            plugin_id=plugin_id,
            user_id=str(current_user.id) if current_user else None,
            enabled=body.enabled,
        )
    except ValueError as exc:
        code = str(exc)
        if code == "unknown_plugin":
            return error_response(404, "插件不存在")
        if code == "internal_plugin_not_installable":
            return error_response(403, "该插件仅内部使用")
        return error_response(400, code)
    return success_response(
        data={"plugin_id": row.plugin_id, "enabled": row.enabled, "version": row.plugin_version}
    )


class ToggleBody(BaseModel):
    enabled: bool


@router.patch("/{plugin_id}/enabled")
def wangcai_toggle(
    plugin_id: str,
    body: ToggleBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PATCH /{plugin_id}/enabled 请求，wangcai相关资源。
    
    :param plugin_id: 参数 plugin_id
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    row = set_plugin_enabled(
        db, tenant_id=str(tenant_id), plugin_id=plugin_id, enabled=body.enabled
    )
    return success_response(data={"plugin_id": row.plugin_id, "enabled": row.enabled})


class RunBody(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    context: dict | None = None


@router.post("/{plugin_id}/run")
def wangcai_run_plugin(
    plugin_id: str,
    body: RunBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /{plugin_id}/run 请求，wangcai相关资源。
    
    :param plugin_id: 参数 plugin_id
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    try:
        data = execute_plugin(
            db,
            tenant_id=str(tenant_id),
            plugin_id=plugin_id,
            message=body.message,
            context=body.context,
            user_id=str(current_user.id) if current_user else None,
        )
    except HermesPluginError as exc:
        if exc.code == "plugin_disabled":
            return error_response(403, "请先在市场安装并启用该插件")
        if exc.code == "unknown_plugin":
            return error_response(404, "插件不存在")
        if exc.code == "gap_not_ready":
            return error_response(501, "插件建设中")
        return error_response(400, str(exc))
    return success_response(data=sanitize_public_data(data))
