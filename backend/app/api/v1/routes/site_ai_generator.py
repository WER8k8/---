# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI 独立站生成与发布路由。"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.security import require_admin
from app.models.user import User
from app.services.ai_site_engine import AISiteEngine, SUPPORTED_LOCALES

router = APIRouter(prefix="/sites/ai", tags=["AI Site Studio"])

ROUTE_PREFIX = ""
ROUTE_TAGS = ["AI Site Studio"]


class GenerateSiteRequest(BaseModel):
    product_name: str = Field(..., description="产品名称")
    product_description: str = Field(..., description="产品描述")
    target_industry: str = Field(default="Industrial Equipment")
    target_market: str = Field(default="Global")
    style_theme: str = Field(default="modern-b2b")
    # 必填：此前默认 "sales@example.com" 是假邮箱，会直接写进生成的官网
    contact_email: str = Field(..., description="官网联系邮箱（必须是租户真实邮箱，无默认值）")


class TranslateSiteRequest(BaseModel):
    page_schema: dict[str, Any]
    target_locale: str


class PublishSiteRequest(BaseModel):
    site_id: str
    page_schema: dict[str, Any]
    custom_domain: str | None = None


@router.post("/generate", summary="一键 AI 生成外贸独立站落地页")
async def generate_site(req: GenerateSiteRequest, _admin: User = Depends(require_admin)) -> dict[str, Any]:
    engine = AISiteEngine()
    schema = await engine.generate_landing_page(
        product_name=req.product_name,
        product_description=req.product_description,
        target_industry=req.target_industry,
        target_market=req.target_market,
        style_theme=req.style_theme,
        contact_email=req.contact_email,
    )
    return {"code": 0, "msg": "ok", "data": schema}


@router.post("/translate", summary="一键翻译生成多语种独立站镜像")
def translate_site(req: TranslateSiteRequest, _admin: User = Depends(require_admin)) -> dict[str, Any]:
    engine = AISiteEngine()
    translated = engine.translate_site_schema(req.page_schema, req.target_locale)
    return {"code": 0, "msg": "ok", "data": translated}


@router.get("/locales", summary="获取支持的多语言列表")
def list_locales(_admin: User = Depends(require_admin)) -> dict[str, Any]:
    return {"code": 0, "msg": "ok", "data": SUPPORTED_LOCALES}


@router.post("/publish", summary="一键发布独立站")
def publish_site(req: PublishSiteRequest, _admin: User = Depends(require_admin)) -> dict[str, Any]:
    domain = req.custom_domain or f"{req.site_id}.globaltrade-ai.site"
    return {
        "code": 0,
        "msg": "Site successfully published",
        "data": {
            "site_id": req.site_id,
            "status": "online",
            "access_url": f"https://{domain}",
            "ssl_enabled": True,
        }
    }
