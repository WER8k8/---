# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI 生成/优化路由 — 统一走场景调度与用量落库。"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps.tenant_quota import consume_tenant_tokens
from app.core.response import error_response, success_response
from app.core.security import get_current_user, optional_auth
from app.db.session import get_db
from app.models.user import User
from app.services.ai_invocation_service import invoke_llm, invoke_optimize, normalize_scenario
from app.services.tenant_scenario_service import resolve_tenant_id_for_user
from app.services.token_service import InsufficientTokenError


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/ai", tags=["AI生成"])


class GenerateRequest(BaseModel):
    prompt: str = ""
    model: str = "general"
    scenario: str | None = None
    max_tokens: int = Field(default=2000, ge=64, le=8000)
    tenant_id: str | None = None
    token_cost: int = 100


class OptimizeRequest(BaseModel):
    content: str = ""
    optimization_type: str = "seo"
    keywords: list[str] = []
    scenario: str | None = "article"
    tenant_id: str | None = None
    token_cost: int = 80


class AiWriteRequest(BaseModel):
    prompt: str = ""
    contentType: str = "video-script"
    scenario: str | None = None


class ProductAIGenerateBody(BaseModel):
    content_type: str = "product"
    keywords: list[str] = Field(default_factory=list)
    product_name: str = ""
    category_name: str = ""
    density: float | None = None
    strength_grade: str = ""
    thermal_conductivity: float | None = None
    fire_rating: str = ""
    existing_description: str = ""


class ProductAIPolishBody(BaseModel):
    content: str = ""
    polish_type: str = "general"


@router.post("/generate")
async def generate_content(
    body: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(optional_auth),
):
    """AI 生成内容（按 scenario 选模型）"""
    tenant_id = resolve_tenant_id_for_user(db, current_user, body.tenant_id) if current_user else body.tenant_id
    bill_tenant = tenant_id or body.tenant_id
    if bill_tenant:
        try:
            consume_tenant_tokens(db, bill_tenant, body.token_cost, "ai_generate")
        except InsufficientTokenError as e:
            return error_response(402, str(e))

    prompt = body.prompt or "请生成一段高质量的建材行业文案"
    scenario = normalize_scenario(body.scenario or body.model or "inference")
    try:
        result = await invoke_llm(
            db,
            prompt=prompt,
            scenario=scenario,
            max_tokens=body.max_tokens,
            tenant_id=tenant_id,
        )
    except RuntimeError as exc:
        return error_response(503, str(exc))

    return success_response(data={**result, "scenario": scenario})


@router.post("/optimize")
async def optimize_content_api(
    body: OptimizeRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(optional_auth),
):
    """AI 优化内容（默认文章场景）"""
    tenant_id = resolve_tenant_id_for_user(db, current_user, body.tenant_id) if current_user else body.tenant_id
    bill_tenant = tenant_id or body.tenant_id
    if bill_tenant:
        try:
            consume_tenant_tokens(db, bill_tenant, body.token_cost, "ai_optimize")
        except InsufficientTokenError as e:
            return error_response(402, str(e))

    content = body.content
    if not content:
        return success_response(
            data={
                "optimized_content": "",
                "changes": [],
                "token_usage": 0,
                "cost": 0,
                "technical_params_preserved": True,
            }
        )

    scenario = normalize_scenario(body.scenario or "article")
    try:
        result = await invoke_optimize(
            db,
            content=content,
            optimization_type=body.optimization_type,
            keywords=body.keywords,
            scenario=scenario,
            tenant_id=tenant_id,
        )
    except RuntimeError as exc:
        return error_response(503, str(exc))

    return success_response(data={**result, "scenario": scenario})


@router.post("/product/generate")
async def product_ai_generate(
    body: ProductAIGenerateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """产品编辑页 — 生成描述/SEO（NVIDIA NIM 场景模型）。"""
    from app.services.product_content_ai_service import generate_product_content
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    try:
        data = await generate_product_content(
            db,
            payload=body.model_dump(),
            tenant_id=tenant_id,
        )
    except RuntimeError as exc:
        return error_response(503, str(exc))
    return success_response(data=data, message="生成成功")


@router.post("/product/polish")
async def product_ai_polish(
    body: ProductAIPolishBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """产品编辑页 — 润色描述/SEO。"""
    from app.services.product_content_ai_service import polish_product_content
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    try:
        data = await polish_product_content(
            db,
            content=body.content,
            polish_type=body.polish_type,
            tenant_id=tenant_id,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    except RuntimeError as exc:
        return error_response(503, str(exc))
    return success_response(data=data, message="润色成功")
