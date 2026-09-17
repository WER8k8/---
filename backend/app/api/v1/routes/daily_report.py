# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""每日经营日报 API"""

from fastapi import APIRouter, Depends, Query

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.daily_report_service import daily_report_service


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/daily-report"
ROUTE_TAGS = ["经营日报"]

router = APIRouter()


@router.get("/")
def get_daily_report(
    current_user: User = Depends(get_current_user),
):
    """获取今日日报"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "l2", "l3"]:
        return error_response(403, "权限不足")
    data = daily_report_service.generate(str(getattr(current_user, "tenant_id", "default")))
    return success_response(data=data)


@router.get("/history")
def get_daily_report_history(
    days: int = Query(7, description="最近天数"),
    current_user: User = Depends(get_current_user),
):
    """获取历史日报列表"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "l2", "l3"]:
        return error_response(403, "权限不足")
    data = daily_report_service.generate_history(str(getattr(current_user, "tenant_id", "default")), days)
    return success_response(data=data)
