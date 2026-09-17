# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""一键建站 API 路由 — POST /api/v1/sites/build。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.services.site_builder.orchestrator import SiteBuilderOrchestrator

logger = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/sites", tags=["一键建站"])


# ── 请求/响应模型 ────────────────────────────────────────────────


class SiteBuildRequest(BaseModel):
    """一键建站请求体。"""
    tenant_id: str | None = Field(
        default=None,
        description="租户 ID（SaaS 多租户场景）",
    )
    product_images: list[str] = Field(
        default_factory=list,
        description="产品图片 URL 列表（可空，无图时退化为纯文本分析）",
    )
    product_description_text: str = Field(
        default="",
        description="产品文字描述（与图片至少填一项）",
    )
    target_market: str = Field(
        default="global",
        description="目标市场（如 '东南亚', '中东', 'global'）",
    )
    language: str = Field(
        default="zh",
        description="站点语言代码（如 'zh', 'en', 'es'）",
    )
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "tenant-001",
                "product_images": [
                    "https://example.com/img1.jpg",
                    "https://example.com/img2.jpg",
                ],
                "product_description_text": "轻集料混凝土，干密度 800kg/m3，导热系数 0.2W/mK",
                "target_market": "东南亚",
                "language": "zh",
            }
        }


class SiteBuildPageResponse(BaseModel):
    """页面级别的建站结果。"""
    page_type: str
    slug: str
    title: str
    meta_description: str = ""
    content_markdown: str = ""
    seo_title: str = ""
    seo_keywords: list[str] = Field(default_factory=list)
    schema_type: str = "Article"
    internal_links: list[dict] = Field(default_factory=list)


class SiteBuildResponse(BaseModel):
    """一键建站响应体。"""
    site_id: str
    tenant_id: str | None = None
    pages: list[SiteBuildPageResponse]
    product_info: dict
    status: str  # success | partial
    steps_completed: list[str]
    steps_failed: list[dict]


# ── 路由 ──────────────────────────────────────────────────────────


@router.post("/build")
async def build_site(
    request: SiteBuildRequest,
    db: Session = Depends(get_db),
):
    """一键建站 — 端到端生成站点结构与内容。

    流程：
    1. Vision 分析产品图片 → 提取特性/参数/应用场景
    2. 生成网站结构 → 确定页面组成
    3. 生成多语言内容 → 每页标题/描述/正文
    4. SEO 优化 → Meta/关键词/Schema/内链
    5. 组装站点数据 → 返回完整页面列表
    """
    # 基础校验
    if not request.product_images and not request.product_description_text.strip():
        return error_response(
            400,
            "product_images 和 product_description_text 至少填写一项",
        )

    try:
        orchestrator = SiteBuilderOrchestrator(
            db,
            tenant_id=request.tenant_id,
        )
        result = await orchestrator.build(
            product_images=request.product_images,
            product_description_text=request.product_description_text,
            target_market=request.target_market,
            language=request.language,
        )
    except Exception as exc:
        logger.exception("Site build failed")
        return error_response(500, f"建站流程异常: {exc}")

    return success_response(
        data=result,
        message="站点生成完成" if result.get("status") == "success" else "站点部分生成（部分步骤失败）",
    )


@router.post("/build/async")
async def build_site_async(
    request: SiteBuildRequest,
    db: Session = Depends(get_db),
):
    """异步建站 — 返回任务 ID，后台执行（预留接口，当前同步返回）。

    未来可接入 Celery/ARQ 实现真正的异步任务队列。
    """
    # TODO: 接入异步任务队列（ARQ / Celery）
    return await build_site(request, db)
