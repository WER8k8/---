"""获客闭环路由。"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.growth_loop_service import GrowthLoopEngine

router = APIRouter(prefix="/growth/campaigns", tags=["Growth Loop Engine"])

ROUTE_PREFIX = "/growth/campaigns"
ROUTE_TAGS = ["Growth Loop Engine"]


class CampaignLaunchRequest(BaseModel):
    tenant_id: str
    campaign_name: str
    target_industry: str
    seed_keywords: list[str] = Field(default_factory=lambda: ["machinery", "parts"])


@router.post("/launch", summary="一键启动全自动化外贸获客战役")
def launch_campaign(req: CampaignLaunchRequest) -> dict[str, Any]:
    engine = GrowthLoopEngine()
    result = engine.run_campaign_pipeline(
        tenant_id=req.tenant_id,
        campaign_name=req.campaign_name,
        target_industry=req.target_industry,
        seed_keywords=req.seed_keywords,
    )
    return {"code": 0, "msg": "Campaign successfully launched", "data": result}
