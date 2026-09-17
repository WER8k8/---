# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""知识库沉淀 API 路由

提供 REST API 接口，将调研结果自动沉淀到知识库。
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

from app.core.security import get_current_user as get_current_active_user
from app.services.knowledge_ingestion import KnowledgeIngestionService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["知识库沉淀"]

router = APIRouter(prefix="/knowledge-ingestion", tags=["知识库沉淀"])
svc = KnowledgeIngestionService()


# ── 请求模型 ──


class MarketReportRequest(BaseModel):
    country: str = Field(..., description="目标国家", min_length=2, max_length=50)
    content: str = Field(..., description="Markdown 调研内容", min_length=50)
    source: str = Field("foreign-trade-research", description="来源")
    metadata: Optional[Dict] = None


class BuyerPersonaRequest(BaseModel):
    persona_name: str = Field(..., description="画像名称", min_length=2, max_length=100)
    content: str = Field(..., description="Markdown 画像内容", min_length=50)
    target_country: str = Field("", description="目标国家")
    source: str = Field("foreign-trade-research", description="来源")


class CompetitorAnalysisRequest(BaseModel):
    competitor_name: str = Field(..., description="竞品名称", min_length=2, max_length=100)
    content: str = Field(..., description="Markdown 分析内容", min_length=50)
    platform: str = Field("", description="平台")
    source: str = Field("foreign-trade-research", description="来源")


class GeoStrategyRequest(BaseModel):
    product_name: str = Field(..., description="产品名称", min_length=2, max_length=100)
    content: str = Field(..., description="Markdown 策略内容", min_length=50)
    ai_engines: Optional[List[str]] = None
    source: str = Field("geo_writing_policy", description="来源")


class EmailTemplateRequest(BaseModel):
    template_name: str = Field(..., description="模板名称", min_length=2, max_length=100)
    content: str = Field(..., description="邮件内容", min_length=20)
    language: str = Field("en", description="语言")
    scenario: str = Field("cold_outreach", description="场景")


class ComplianceInfoRequest(BaseModel):
    country: str = Field(..., description="目标国家", min_length=2, max_length=50)
    product: str = Field(..., description="产品名称", min_length=2, max_length=100)
    content: str = Field(..., description="Markdown 合规信息", min_length=50)
    source: str = Field("foreign-trade-research", description="来源")


class ResearchReportRequest(BaseModel):
    title: str = Field(..., description="报告标题", min_length=2, max_length=200)
    content: str = Field(..., description="Markdown 报告内容", min_length=100)
    report_type: str = Field("general", description="报告类型")
    source: str = Field("deerflow", description="来源")


# ── API 路由 ──


@router.post("/market-report", summary="沉淀市场调研报告")
async def ingest_market_report(
    req: MarketReportRequest,
    user=Depends(get_current_active_user),
):
    """将市场调研报告保存到知识库"""
    path = svc.ingest_market_report(
        country=req.country,
        content=req.content,
        source=req.source,
        metadata=req.metadata,
    )
    return {"status": "ok", "path": path, "message": f"已沉淀 {req.country} 市场报告"}


@router.post("/buyer-persona", summary="沉淀买家画像")
async def ingest_buyer_persona(
    req: BuyerPersonaRequest,
    user=Depends(get_current_active_user),
):
    """将买家画像保存到知识库"""
    path = svc.ingest_buyer_persona(
        persona_name=req.persona_name,
        content=req.content,
        target_country=req.target_country,
        source=req.source,
    )
    return {"status": "ok", "path": path, "message": f"已沉淀买家画像: {req.persona_name}"}


@router.post("/competitor-analysis", summary="沉淀竞品分析")
async def ingest_competitor_analysis(
    req: CompetitorAnalysisRequest,
    user=Depends(get_current_active_user),
):
    """将竞品分析保存到知识库"""
    path = svc.ingest_competitor_analysis(
        competitor_name=req.competitor_name,
        content=req.content,
        platform=req.platform,
        source=req.source,
    )
    return {"status": "ok", "path": path, "message": f"已沉淀竞品分析: {req.competitor_name}"}


@router.post("/geo-strategy", summary="沉淀 GEO 策略")
async def ingest_geo_strategy(
    req: GeoStrategyRequest,
    user=Depends(get_current_active_user),
):
    """将 GEO 优化策略保存到知识库"""
    path = svc.ingest_geo_strategy(
        product_name=req.product_name,
        content=req.content,
        ai_engines=req.ai_engines,
        source=req.source,
    )
    return {"status": "ok", "path": path, "message": f"已沉淀 GEO 策略: {req.product_name}"}


@router.post("/email-template", summary="沉淀邮件模板")
async def ingest_email_template(
    req: EmailTemplateRequest,
    user=Depends(get_current_active_user),
):
    """将邮件模板保存到知识库"""
    path = svc.ingest_email_template(
        template_name=req.template_name,
        content=req.content,
        language=req.language,
        scenario=req.scenario,
    )
    return {"status": "ok", "path": path, "message": f"已沉淀邮件模板: {req.template_name}"}


@router.post("/compliance", summary="沉淀合规认证信息")
async def ingest_compliance_info(
    req: ComplianceInfoRequest,
    user=Depends(get_current_active_user),
):
    """将合规认证信息保存到知识库"""
    path = svc.ingest_compliance_info(
        country=req.country,
        product=req.product,
        content=req.content,
        source=req.source,
    )
    return {"status": "ok", "path": path, "message": f"已沉淀合规信息: {req.product} → {req.country}"}


@router.post("/research-report", summary="沉淀通用调研报告")
async def ingest_research_report(
    req: ResearchReportRequest,
    user=Depends(get_current_active_user),
):
    """将通用调研报告保存到知识库"""
    path = svc.ingest_research_report(
        title=req.title,
        content=req.content,
        report_type=req.report_type,
        source=req.source,
    )
    return {"status": "ok", "path": path, "message": f"已沉淀报告: {req.title}"}


@router.get("/stats", summary="知识库统计")
async def get_stats(user=Depends(get_current_active_user)):
    """获取知识库统计信息"""
    return svc.get_stats()


@router.get("/files", summary="知识库文件列表")
async def list_files(
    category: Optional[str] = None,
    user=Depends(get_current_active_user),
):
    """列出知识库文件"""
    return svc.list_knowledge_files(category=category)
