# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""知识库 API 路由"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.knowledge_service import KnowledgeService
from app.services.rag_pricing_guard import validate_sales_text


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/knowledge"
ROUTE_TAGS = ["知识库"]

router = APIRouter(tags=["知识库"])


class ValidateQuoteBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    min_price: float | None = Field(None, ge=0)
    max_price: float | None = Field(None, ge=0)
    currency_hint: str = "CNY"

# 知识库服务单例
_knowledge_service: KnowledgeService | None = None


def _get_service() -> KnowledgeService:
    """获取或初始化知识库服务"""
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
    return _knowledge_service


@router.get("/categories")
def get_categories():
    """获取知识库分类列表"""
    service = _get_service()
    categories = service.get_categories()
    return success_response(data={"categories": categories})


@router.get("/search")
def search_knowledge(
    q: str = Query("", description="搜索关键词"),
    top_k: int = Query(5, description="返回结果数量", ge=1, le=20),
):
    """搜索相关知识"""
    service = _get_service()
    results = service.search(q, top_k=top_k)
    return success_response(data={
        "results": results,
        "total": len(results),
    })


@router.post("/ask")
def ask_knowledge(
    question: str = Query(..., description="用户问题"),
):
    """基于知识库回答问题"""
    service = _get_service()
    result = service.ask(question)
    return success_response(data=result)


@router.get("/info")
def get_knowledge_info():
    """获取知识库概览信息"""
    service = _get_service()
    info = service.get_knowledge_base_info()
    return success_response(data=info)


@router.post("/validate-quote")
def validate_quote_text(
    body: ValidateQuoteBody,
    current_user: User = Depends(get_current_user),
):
    """校验销售/AI 话术是否含乱报价或违规承诺（租户 RAG 护栏）。"""
    if current_user.role not in ("admin", "super_admin", "tenant_admin", "sales"):
        return error_response(403, "权限不足")
    if (
        body.min_price is not None
        and body.max_price is not None
        and body.min_price > body.max_price
    ):
        return error_response(400, "min_price 不能大于 max_price")
    result = validate_sales_text(
        body.text,
        min_price=body.min_price,
        max_price=body.max_price,
        currency_hint=body.currency_hint,
    )
    return success_response(data=result.to_dict())
