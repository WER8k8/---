# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import optional_auth
from app.models.user import User
from app.services.ai_invocation_service import invoke_optimize, normalize_scenario
from app.services.tenant_scenario_service import resolve_tenant_id_for_user
from app.services.content_optimizer import ContentOptimizer

router = APIRouter()


class OptimizeRequest(BaseModel):
    content: str = ""
    title: str = ""
    description: str = ""
    optimization_type: str = "content"
    opt_type: str = ""
    keywords: list[str] = []
    model: str = "article"
    scenario: str | None = "article"


class ValidateRequest(BaseModel):
    original: str
    optimized: str


@router.post("/optimize")
async def optimize_content(
        req: OptimizeRequest,
        db: Session = Depends(get_db),
        current_user: User | None = Depends(optional_auth)):
    """optimize_content。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    content_to_optimize = req.content or req.title or req.description
    if not content_to_optimize:
        raise HTTPException(status_code=400, detail="请提供要优化的内容、标题或描述")

    opt_type = req.optimization_type or req.opt_type or "content"
    if opt_type not in ["title", "description", "alt_text", "content"]:
        raise HTTPException(
            status_code=400,
            detail="优化类型不支持，支持: title/description/alt_text/content")

    scenario = normalize_scenario(req.scenario or req.model or "article")
    tenant_id = resolve_tenant_id_for_user(db, current_user) if current_user else None
    try:
        return await invoke_optimize(
            db,
            content=content_to_optimize,
            optimization_type=opt_type,
            keywords=req.keywords,
            scenario=scenario,
            tenant_id=tenant_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/validate-content")
def validate_content(
        req: ValidateRequest,
        current_user: User = Depends(optional_auth)):
    """validate_content。

    参数说明：
    :param req: 参数 req
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    optimizer = ContentOptimizer()
    result = optimizer.validate_compliance(req.original, req.optimized)
    return result


class ExtractParamsRequest(BaseModel):
    content: str


@router.post("/extract-params")
def extract_params(req: ExtractParamsRequest,
                   current_user: User = Depends(optional_auth)):
    """extract_params。

    参数说明：
    :param req: 参数 req
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    optimizer = ContentOptimizer()
    params = optimizer.extract_technical_params(req.content)
    return {"technical_params": params, "found": len(params) > 0}
