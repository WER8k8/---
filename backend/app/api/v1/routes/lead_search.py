# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""线索搜索引擎 API — FIX-61

倒排索引 + 向量搜索混合引擎：
- 索引管理（添加/批量索引/删除）
- 关键词搜索（倒排索引）
- 混合搜索（倒排 + 向量加权）
- 搜索建议（自动补全）
- 引擎统计
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.core.response import success_response, error_response
from app.services.ubrain.lead_search_engine import lead_search_engine


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["线索搜索引擎"]

router = APIRouter(prefix="/lead-search", tags=["线索搜索引擎"])


@router.post("/index")
def index_lead(
    lead_id: str = Query(..., description="线索ID"),
    fields: dict[str, Any] = None,
    current_user=Depends(get_current_user),
):
    """索引一条线索到搜索引擎。"""
    if not lead_search_engine.is_initialized:
        lead_search_engine.initialize()

    lead_search_engine.index_lead(lead_id, fields or {})
    return success_response(data={"indexed": lead_id, "total": lead_search_engine.stats()["total_docs"]})


@router.post("/index/batch")
def index_batch(
    leads: list[dict[str, Any]],
    current_user=Depends(get_current_user),
):
    """批量索引线索。"""
    if not lead_search_engine.is_initialized:
        lead_search_engine.initialize()

    count = lead_search_engine.index_batch(leads)
    return success_response(data={"indexed_count": count, "total": lead_search_engine.stats()["total_docs"]})


@router.post("/index/remove")
def remove_lead(
    lead_id: str = Query(..., description="线索ID"),
    current_user=Depends(get_current_user),
):
    """从索引中移除线索。"""
    if not lead_search_engine.is_initialized:
        lead_search_engine.initialize()

    lead_search_engine._inverted.remove(lead_id)
    return success_response(data={"removed": lead_id, "total": lead_search_engine.stats()["total_docs"]})


@router.get("/search")
def search_leads(
    q: str = Query(..., description="搜索关键词"),
    field: str = Query("", description="限定搜索字段（company_name/title/email/industry）"),
    top_k: int = Query(50, ge=1, le=200, description="最多返回数"),
    use_vector: bool = Query(False, description="是否启用向量搜索（混合模式）"),
    vector_weight: float = Query(0.3, ge=0.0, le=1.0, description="向量搜索权重"),
    current_user=Depends(get_current_user),
):
    """搜索线索（倒排索引 + 可选向量搜索）。"""
    if not lead_search_engine.is_initialized:
        lead_search_engine.initialize()

    results = lead_search_engine.search(
        query=q,
        field=field,
        top_k=top_k,
        use_vector=use_vector,
        vector_weight=vector_weight,
    )
    return success_response(data={
        "query": q,
        "total_hits": len(results),
        "results": [r.to_dict() for r in results],
    })


@router.get("/suggest")
def suggest(
    prefix: str = Query(..., min_length=1, description="输入前缀"),
    field: str = Query("", description="限定字段"),
    limit: int = Query(10, ge=1, le=50, description="最多返回数"),
    current_user=Depends(get_current_user),
):
    """搜索自动补全建议。"""
    if not lead_search_engine.is_initialized:
        lead_search_engine.initialize()

    suggestions = lead_search_engine.suggest(prefix=prefix, field=field, limit=limit)
    return success_response(data={"prefix": prefix, "suggestions": suggestions})


@router.get("/stats")
def engine_stats(current_user=Depends(get_current_user)):
    """获取搜索引擎统计信息。"""
    if not lead_search_engine.is_initialized:
        lead_search_engine.initialize()

    return success_response(data=lead_search_engine.stats())


@router.post("/initialize")
def initialize_engine(current_user=Depends(get_current_user)):
    """初始化搜索引擎。"""
    lead_search_engine.initialize()
    return success_response(data={"initialized": True, "stats": lead_search_engine.stats()})