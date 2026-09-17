# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客闭环路由。"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.growth_loop_service import GrowthLoopEngine
from app.services.tenant_scenario_service import resolve_tenant_id_for_user

router = APIRouter(prefix="/growth/campaigns", tags=["Growth Loop Engine"])

ROUTE_PREFIX = ""
ROUTE_TAGS = ["Growth Loop Engine"]


class CampaignLaunchRequest(BaseModel):
    tenant_id: str
    campaign_name: str
    target_industry: str
    seed_keywords: list[str] = Field(default_factory=lambda: ["machinery", "parts"])


@router.post("/launch", summary="一键启动全自动化外贸获客战役")
def launch_campaign(
    req: CampaignLaunchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    # 租户越权防护：普通用户强制使用自身租户，admin/super_admin 可指定
    tenant_id = (
        req.tenant_id
        if current_user.role in ("super_admin", "admin")
        else resolve_tenant_id_for_user(db, current_user)
    )
    engine = GrowthLoopEngine()
    result = engine.run_campaign_pipeline(
        tenant_id=tenant_id,
        campaign_name=req.campaign_name,
        target_industry=req.target_industry,
        seed_keywords=req.seed_keywords,
    )
    return {"code": 0, "msg": "Campaign successfully launched", "data": result}
