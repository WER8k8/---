# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
获客全链路极智升维 API 路由 (Ultimate Acquisition Pipeline Routes)。

包含：
1. 360° 全球买家画像透视与反查
2. AI 极智千人千面多语种破冰开发信工坊
3. 7 步出海高转化节奏编排器
4. 外贸 8 大经典抗拒智能谈判助攻中枢
5. 线索一键无缝跃迁至 BOQ 工业核价与履约 PI
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.response import success_response
from app.services.acquisition import (
    Buyer360EnrichmentEngine,
    AIPitchStudio,
    OutboundCadenceEngine,
    ObjectionCopilot,
)

ROUTE_PREFIX = ""

router = APIRouter(prefix="/acquisition-pipeline", tags=["外贸获客全链路极智升维"])


# ── 请求与响应 Pydantic 模型 ─────────────────────────────────────
class EnrichBuyerRequest(BaseModel):
    company_name: str = Field(..., min_length=1, description="目标买家公司名称，如 Al Fozan Group")
    domain: Optional[str] = Field("", description="买家官方网址或域名")
    country: Optional[str] = Field("SA", description="国家二字码或名称，如 SA, AE, US, DE")
    industry_hint: Optional[str] = Field("stone", description="品类偏好提示 (stone/ceramic/steel/wood/glass)")


class GeneratePitchRequest(BaseModel):
    company_name: str = Field(..., min_length=1, description="目标公司名称")
    country: Optional[str] = Field("Saudi Arabia", description="目标国家")
    product_category: Optional[str] = Field("Porcelain Tiles & Marble Slabs", description="产品主推品类")
    contact_person: Optional[str] = Field("Procurement Director", description="决策人称呼/职务")
    pain_point: Optional[str] = Field("Lead time delays and container overweight risks", description="买家核心痛点")
    research_level: Optional[str] = Field("basic", description="背调等级 (none/basic/osint/full)")
    language: Optional[str] = Field("en", description="语言 (en/ar/es/ru/pt/fr)")


class CadencePlanRequest(BaseModel):
    company_name: str = Field(..., min_length=1, description="买家公司名称")
    country: Optional[str] = Field("SA", description="目标国家二字码 (SA/AE/DE/US/IN)")
    product_category: Optional[str] = Field("Ceramic & Stone", description="主打建材品类")


class ObjectionAssistRequest(BaseModel):
    objection_key: str = Field("price_high", description="抗拒场景 key，如 price_high, long_oa, quality_cert 等")


class HandoffToQuoteRequest(BaseModel):
    lead_id: Optional[str] = Field("", description="线索编号或询盘编号")
    buyer_name: str = Field(..., description="买家公司名称")
    country: Optional[str] = Field("SA", description="国家")
    product_category: Optional[str] = Field("marble", description="品类 (marble, granite, ceramic, steel)")
    target_port: Optional[str] = Field("Jeddah Islamic Port", description="目的港")
    estimated_sqm: Optional[float] = Field(1200.0, description="预估采购数量 (SQM 或 Unit)")


# ── 端点实现 ──────────────────────────────────────────────────
@router.post("/enrich-buyer", summary="360° 全球买家深度画像透视反查")
async def enrich_buyer(req: EnrichBuyerRequest):
    """根据公司名、域名与国家，秒级反查采购体量、目的港、决策树与合规风险。"""
    intelligence = Buyer360EnrichmentEngine.enrich_buyer(
        company_name=req.company_name,
        domain=req.domain or "",
        country=req.country or "SA",
        industry_hint=req.industry_hint or "stone",
    )
    return success_response(data=intelligence)


@router.post("/generate-pitch", summary="AI 极智千人千面多语种破冰开发信工坊")
async def generate_pitch(req: GeneratePitchRequest):
    """遵循 P1-6 严格背调门禁，生成 Cold Email、WhatsApp 黄金 3 行钩子与 LinkedIn 邀约。"""
    pitch_data = AIPitchStudio.generate_pitch(
        company_name=req.company_name,
        country=req.country or "Saudi Arabia",
        product_category=req.product_category or "Porcelain Tiles & Marble Slabs",
        contact_person=req.contact_person or "Procurement Director",
        pain_point=req.pain_point or "Lead time delays and container overweight risks",
        research_level=req.research_level or "basic",
        language=req.language or "en",
    )
    return success_response(data=pitch_data)


@router.post("/cadence-plan", summary="7 步出海高转化节奏时区编排器")
async def cadence_plan(req: CadencePlanRequest):
    """基于目标国本地工作日与黄金投递时隙，生成 30 天 7 轮多通道跟进节奏。"""
    plan = OutboundCadenceEngine.generate_cadence_plan(
        company_name=req.company_name,
        country=req.country or "SA",
        product_category=req.product_category or "Ceramic & Stone",
    )
    return success_response(data=plan)


@router.get("/objections", summary="获取外贸 8 大经典抗拒场景列表")
async def list_objections():
    """获取外贸销售中最常见的 8 种被拒绝/被压价抗拒场景清单。"""
    items = ObjectionCopilot.list_all_objections()
    return success_response(data={"objections": items})


@router.post("/objection-assist", summary="外贸 8 大异议智能反击与谈判助攻")
async def objection_assist(req: ObjectionAssistRequest):
    """输入抗拒类型，秒级获取资深老外贸反击战术、双语话术与底牌置换条件。"""
    solution = ObjectionCopilot.get_objection_solution(req.objection_key)
    return success_response(data=solution)


@router.post("/handoff-to-quote", summary="线索一键跃迁至 BOQ 22 参数工业核价与履约")
async def handoff_to_quote(req: HandoffToQuoteRequest):
    """把选中的海外潜客直接转换为预填好的 BOQ 22 参数核价单，并产出跳转载荷。"""
    boq_prefill = {
        "client_name": req.buyer_name,
        "destination_country": req.country,
        "destination_port": req.target_port,
        "material_type": req.product_category,
        "thickness_mm": 20,
        "quality_grade": "A",
        "surface_finish": "polished",
        "edge_processing": "straight",
        "quantity_sqm": req.estimated_sqm,
        "incoterms": "CIF",
        "loading_port": "Xiamen Port",
        "packaging": "wooden_crate",
        "transit_insurance": True,
        "inspection_service": True,
        "recommended_route": f"/client/export-quote?buyer={req.buyer_name}&country={req.country}&material={req.product_category}",
        "message": "已生成 BOQ 22 参数预填数据，可直通工业核价台与外贸 7 步履约队列！",
    }
    return success_response(data=boq_prefill)
