# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Plan Gate BFF — 只读校验出口"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.plan_gate_service import evaluate_feature_access, evaluate_route_access
from app.api.v1.admin_bff.user_context import load_tenant_for_user

router = APIRouter()


@router.get("/check")
async def check_plan_feature(
    feature: str | None = Query(None),
    route: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """check_plan_feature。

    参数说明：
    :param feature: 参数 feature
    :param route: 参数 route
    :param user: 参数 user
    :param db: 参数 db
    :return: 返回处理结果。
    """
    tenant = load_tenant_for_user(db, user)
    if route:
        result = evaluate_route_access(tenant, route)
        if result is None:
            return success_response(data={"allowed": True, "feature_key": None})
        return success_response(data=result)
    if not feature:
        return error_response(400, "请提供 feature 或 route 参数")
    return success_response(data=evaluate_feature_access(tenant, feature))
