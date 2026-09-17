# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
询盘 API v2 兼容层 — 全部转发至 /api/v1/inquiries/unified（T-P0-14）。
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.inquiries_unified_service import InquiriesUnifiedService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/inquiries-v2"
ROUTE_TAGS = ["询盘管理(兼容旧路径)"]

router = APIRouter(tags=["inquiries(兼容旧路径)"])

_CANONICAL = "/api/v1/inquiries/unified"


def _deprecated(response: Response) -> None:
    """_deprecated。

    参数说明：
    :param response: 参数 response
    :return: 返回处理结果。
    """
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = f'<{_CANONICAL}>; rel="successor-version"'


@router.get("/")
def list_inquiries_v2_compat(
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    buyer_id: Optional[str] = None,
    merchant_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """兼容旧 inquiries-v2 列表 → unified。"""
    _deprecated(response)
    if page < 1:
        page = 1
    effective_page = page if skip == 0 else max(1, (skip // max(limit, 1)) + 1)
    effective_size = page_size if page_size != 20 else min(limit, 100)
    data = InquiriesUnifiedService(db).list_page(
        page=effective_page,
        page_size=effective_size,
        status=status,
    )
    data["deprecated"] = True
    data["use_instead"] = _CANONICAL
    return success_response(data=data)


@router.get("/{inquiry_id}")
def get_inquiry_v2_compat(
    inquiry_id: str,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """get_inquiry_v2_compat。

    参数说明：
    :param inquiry_id: 参数 inquiry_id
    :param response: 参数 response
    :param db: 参数 db
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    _deprecated(response)
    from app.api.v1.routes.inquiries import get_inquiry
    return get_inquiry(inquiry_id, db, current_user)


@router.post("/")
def create_inquiry_v2_compat(
    response: Response,
    db: Session = Depends(get_db),
):
    """create_inquiry_v2_compat。

    参数说明：
    :param response: 参数 response
    :param db: 参数 db
    :return: 返回处理结果。
    """
    _deprecated(response)
    return error_response(
        410,
        "请使用 POST /api/v1/inquiries/public 提交询盘",
        data={"use_instead": "/api/v1/inquiries/public"},
    )
