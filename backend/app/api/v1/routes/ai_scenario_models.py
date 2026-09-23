# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI 场景模型兼容别名 `/ai/scenario-models`（B5）：真身是 `/tenants/self/ai-scenarios`。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import get_current_user
from app.models.user import User

ROUTE_PREFIX = "/ai"
ROUTE_TAGS = ["AI场景模型"]

router = APIRouter(tags=["AI场景模型"])


@router.get("/scenario-models")
def get_ai_scenario_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """兼容别名 → 租户 AI 场景配置。"""
    from app.api.v1.routes.tenants import _tenant_for_user
    from app.services.tenant_scenario_service import build_tenant_scenario_payload

    tenant, err = _tenant_for_user(db, current_user)
    if err:
        return err
    data = build_tenant_scenario_payload(db, tenant)
    if isinstance(data, dict):
        data.setdefault("alias_of", "/tenants/self/ai-scenarios")
    return success_response(data=data)


@router.put("/scenario-models")
def update_ai_scenario_models(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """兼容别名：写回租户 AI 场景覆盖。"""
    from app.api.v1.routes.tenants import _tenant_for_user
    from app.services.tenant_scenario_service import (
        build_tenant_scenario_payload,
        write_tenant_overrides,
    )

    tenant, err = _tenant_for_user(db, current_user)
    if err:
        return err
    overrides = body.get("overrides") if isinstance(body, dict) else None
    write_tenant_overrides(db, tenant, overrides or {})
    data = build_tenant_scenario_payload(db, tenant)
    if isinstance(data, dict):
        data.setdefault("alias_of", "/tenants/self/ai-scenarios")
    return success_response(data=data, message="场景模型已保存")
