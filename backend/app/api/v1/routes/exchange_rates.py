# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""汇率只读端点（GJ-U3 · GoodJob 上游同源）。

GET /exchange-rates/latest：当日参考汇率（Frankfurter/ECB，USD 基准四货币对）。
数据源不可用时 available=False（fail-closed），绝不伪造数值。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.response import success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services import exchange_rate_service as svc

router = APIRouter(prefix="/exchange-rates", tags=["汇率"])


@router.get("/latest")
def latest_rates(current_user: User = Depends(get_current_user)):
    """当日汇率（15 分钟缓存；fail-closed）。"""
    data = svc.get_latest()
    return success_response(data=data)
