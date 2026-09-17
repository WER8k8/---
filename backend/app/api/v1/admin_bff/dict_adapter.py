# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""字典 BFF — 只读配置出口"""

from fastapi import APIRouter

from app.api.v1.admin_bff.plan_catalog import PLAN_FEATURES
from app.core.response import success_response

router = APIRouter()


@router.get("/plan_features")
async def get_plan_features():
    """get_plan_features。
    :return: 返回处理结果。
    """
    return success_response(data=PLAN_FEATURES)
