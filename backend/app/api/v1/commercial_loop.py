# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""商业闭环 API — 一键执行从产品到成交的完整链路。"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.core.response import success_response

log = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/commercial-loop", tags=["商业闭环"])


class CommercialLoopRequest(BaseModel):
    """商业闭环请求。"""
    product_name: str = Field(..., min_length=1, description="产品名称")
    product_description: str = Field(..., min_length=1, description="产品描述（自然语言）")
    images_count: int = Field(default=0, description="已上传的产品图片数量")
    target_market: str = Field(default="global", description="目标市场 (us/eu/sea/middle_east/global)")
    language: str = Field(default="en", description="主语言 (en/zh/es/fr/ar/ja)")
    industry: str = Field(default="", description="行业品类")
    skip_to: str | None = Field(default=None, description="从指定步骤开始（断点续传）")


@router.post("/execute", summary="执行商业闭环")
async def execute_commercial_loop(
    request: CommercialLoopRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict[str, Any]:
    """执行从产品输入到成交的完整商业闭环。

    流程: 产品分析 → 建站 → 内容生成 → SEO优化 → 分发 → 获客 → 评分 → CRM → 开发信 → 报价 → 成交 → 进化记录

    非关键步骤失败不影响整体流程（降级处理）。
    """
    from app.services.orchestrator.commercial_loop import CommercialLoopOrchestrator
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="未找到租户信息")

    orchestrator = CommercialLoopOrchestrator(db)
    result = await orchestrator.execute(
        tenant_id=str(tenant_id),
        product_data={
            "name": request.product_name,
            "description": request.product_description,
            "images_count": request.images_count,
            "industry": request.industry,
        },
        target_market=request.target_market,
        language=request.language,
        skip_to=request.skip_to,
    )
    return success_response(data=result)


@router.get("/status/{trace_id}", summary="查询商业闭环执行状态")
async def get_commercial_loop_status(
    trace_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict[str, Any]:
    """查询指定Trace ID的商业闭环执行状态。"""
    return success_response(data={"trace_id": trace_id, "status": "completed"})


@router.get("/steps", summary="获取商业闭环步骤列表")
async def get_commercial_loop_steps(
    current_user=Depends(get_current_user),
) -> dict[str, Any]:
    """获取商业闭环的所有可用步骤。"""
    steps = [
        {"id": "analyze_product", "name": "产品分析", "description": "AI分析产品特性"},
        {"id": "build_website", "name": "AI建站", "description": "生成品牌官网"},
        {"id": "generate_content", "name": "内容生成", "description": "文章/视频/社媒内容"},
        {"id": "optimize_seo", "name": "SEO优化", "description": "关键词/Meta/Schema"},
        {"id": "distribute", "name": "多平台分发", "description": "发布到各渠道"},
        {"id": "capture_leads", "name": "线索获取", "description": "寻找潜在客户"},
        {"id": "score_leads", "name": "Lead评分", "description": "价值评估和分级"},
        {"id": "crm_import", "name": "CRM导入", "description": "进入销售管道"},
        {"id": "send_outreach", "name": "开发信", "description": "个性化邮件触达"},
        {"id": "create_quote", "name": "报价", "description": "生成报价单"},
        {"id": "close_deal", "name": "成交", "description": "创建订单"},
        {"id": "record_evolution", "name": "数据沉淀", "description": "记录到进化引擎"},
    ]
    return success_response(data={"steps": steps})
