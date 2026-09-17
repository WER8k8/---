# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""跨平台数据看板 API — 聚合 AiToEarn 各平台数据。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.core.tenant_access import assert_user_tenant_active, is_platform_admin, is_tenant_staff
from app.models.user import User
from app.services import cross_platform_dashboard_service as svc
from app.services.tenant_scenario_service import resolve_tenant_id_for_user

router = APIRouter()


def _guard_dashboard(user: User, db: Session):
    """
    处理 _guard_dashboard 相关业务逻辑。

    :param user: 入参 (User)。
    :param db: 入参 (Session)。

    :return: 返回处理结果（或 None）。
    """
    if is_platform_admin(user):
        return None
    if is_tenant_staff(user):
        try:
            assert_user_tenant_active(user, db)
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else "权限不足"
            return error_response(int(exc.status_code), detail)
        return None
    return error_response(403, "权限不足")


def _tenant_scope(db: Session, user: User) -> str | None:
    """
    处理 _tenant_scope 相关业务逻辑。

    :param db: 入参 (Session)。
    :param user: 入参 (User)。

    :return: 返回 str | None 类型的结果。
    """
    if is_platform_admin(user):
        return None
    return resolve_tenant_id_for_user(db, user)


@router.get("/overview")
async def platform_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """跨平台数据概览（账号/粉丝/作品/互动汇总）。"""
    denied = _guard_dashboard(current_user, db)
    if denied:
        return denied

    tenant_id = _tenant_scope(db, current_user)
    try:
        data = await svc.get_platform_overview(tenant_id=tenant_id)
        return success_response(data=data)
    except Exception as exc:
        return error_response(500, f"获取数据失败: {str(exc)[:200]}")


@router.get("/nurture")
async def nurture_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """养号效果看板（周期进度/互动完成率/状态统计）。"""
    denied = _guard_dashboard(current_user, db)
    if denied:
        return denied

    tenant_id = _tenant_scope(db, current_user)
    try:
        data = await svc.get_nurture_dashboard(tenant_id=tenant_id)
        return success_response(data=data)
    except Exception as exc:
        return error_response(500, f"获取数据失败: {str(exc)[:200]}")


@router.get("/publish")
async def publish_dashboard(
    days: int = Query(default=7, ge=1, le=90, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布效果看板（成功率/平台分布/最近任务）。"""
    denied = _guard_dashboard(current_user, db)
    if denied:
        return denied

    tenant_id = _tenant_scope(db, current_user)
    try:
        data = await svc.get_publish_dashboard(tenant_id=tenant_id, days=days)
        return success_response(data=data)
    except Exception as exc:
        return error_response(500, f"获取数据失败: {str(exc)[:200]}")


@router.get("/summary")
async def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """看板汇总（概览 + 养号 + 发布 三合一）。"""
    denied = _guard_dashboard(current_user, db)
    if denied:
        return denied

    tenant_id = _tenant_scope(db, current_user)
    try:
        overview = await svc.get_platform_overview(tenant_id=tenant_id)
        nurture = await svc.get_nurture_dashboard(tenant_id=tenant_id)
        publish = await svc.get_publish_dashboard(tenant_id=tenant_id, days=7)
        return success_response(data={
            "overview": overview,
            "nurture": nurture,
            "publish": publish,
        })
    except Exception as exc:
        return error_response(500, f"获取数据失败: {str(exc)[:200]}")
