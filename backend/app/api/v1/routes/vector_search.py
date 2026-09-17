# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Vector Search API - 向量检索路由

端点：
- POST /vector/search       向量搜索
- POST /vector/upsert       插入/更新向量
- POST /vector/hybrid-search 混合搜索（关键词 + 向量）
- DELETE /vector/{collection}/{point_id} 删除向量
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.response import success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.ubrain.embedding_service import get_embedding_service
from app.services.ubrain.vector_search_service import get_vector_search_service

logger = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["向量检索"]

router = APIRouter(prefix="/vector", tags=["向量检索"])

# ── 请求/响应模型 ──


class VectorSearchRequest(BaseModel):
    """向量搜索请求"""
    collection: str = Field(..., description="集合名称")
    query_text: Optional[str] = Field(None, description="查询文本（如提供则自动 Embedding）")
    query_vector: Optional[list[float]] = Field(None, description="查询向量（与 query_text 二选一）")
    top_k: int = Field(10, ge=1, le=100, description="返回结果数")
    filters: Optional[dict[str, Any]] = Field(None, description="过滤条件，如 {'status': 'active'}")
    model: Optional[str] = Field(None, description="覆盖默认 Embedding 模型")


class VectorUpsertRequest(BaseModel):
    """向量插入/更新请求"""
    collection: str = Field(..., description="集合名称")
    texts: Optional[list[str]] = Field(None, description="文本列表（自动 Embedding）")
    vectors: Optional[list[list[float]]] = Field(None, description="向量列表（与 texts 二选一）")
    payloads: Optional[list[dict[str, Any]]] = Field(None, description="每条向量的附加数据")
    ids: Optional[list[str]] = Field(None, description="自定义 ID")
    model: Optional[str] = Field(None, description="覆盖默认 Embedding 模型")


class HybridSearchRequest(BaseModel):
    """混合搜索请求"""
    collection: str = Field(..., description="集合名称")
    query_text: str = Field(..., description="查询文本")
    top_k: int = Field(10, ge=1, le=100, description="返回结果数")
    text_boost: float = Field(0.3, ge=0.0, le=1.0, description="文本匹配权重")
    model: Optional[str] = Field(None, description="覆盖默认 Embedding 模型")


class VectorDeleteRequest(BaseModel):
    """向量删除请求（批量）"""
    collection: str = Field(..., description="集合名称")
    point_ids: list[str] = Field(..., description="要删除的 point ID 列表")


# ── 辅助函数 ──


def _get_or_generate_vector(
    query_text: Optional[str],
    query_vector: Optional[list[float]],
    model: Optional[str],
) -> list[float]:
    """获取查询向量：优先使用传入的向量，否则通过文本生成"""
    if query_vector is not None and len(query_vector) > 0:
        return query_vector
    if query_text:
        emb_service = get_embedding_service()
        return emb_service.generate_embedding(query_text, model=model)
    raise HTTPException(status_code=422, detail="必须提供 query_text 或 query_vector")


# ── 路由端点 ──


@router.post("/search")
def vector_search(
    req: VectorSearchRequest,
    user: User = Depends(get_current_user),
):
    """向量相似度搜索

    支持直接传入 query_vector，或传入 query_text 由服务自动 Embedding。
    """
    try:
        query_vector = _get_or_generate_vector(
            req.query_text, req.query_vector, req.model
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("生成查询向量失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"生成查询向量失败: {exc}")

    service = get_vector_search_service()
    try:
        results = service.search(
            collection_name=req.collection,
            query_vector=query_vector,
            top_k=req.top_k,
            filters=req.filters,
        )
        return success_response(
            data={
                "results": results,
                "collection": req.collection,
                "top_k": req.top_k,
            }
        )
    except Exception as exc:
        logger.error("向量搜索失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"向量搜索失败: {exc}")


@router.post("/upsert")
def vector_upsert(
    req: VectorUpsertRequest,
    user: User = Depends(get_current_user),
):
    """插入或更新向量

    支持传入 texts（自动 Embedding）或 vectors（直接使用）。
    """
    vectors: list[list[float]] = []
    if req.vectors:
        vectors = req.vectors
    elif req.texts:
        emb_service = get_embedding_service()
        try:
            vectors = emb_service.generate_batch_embeddings(req.texts, model=req.model)
        except Exception as exc:
            logger.error("批量生成 Embedding 失败: %s", exc)
            raise HTTPException(status_code=500, detail=f"Embedding 生成失败: {exc}")
    else:
        raise HTTPException(status_code=422, detail="必须提供 texts 或 vectors")

    service = get_vector_search_service()
    try:
        result = service.upsert_vectors(
            collection_name=req.collection,
            vectors=vectors,
            payloads=req.payloads,
            ids=req.ids,
        )
        return success_response(data=result)
    except Exception as exc:
        logger.error("向量 upsert 失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"向量 upsert 失败: {exc}")


@router.post("/hybrid-search")
def vector_hybrid_search(
    req: HybridSearchRequest,
    user: User = Depends(get_current_user),
):
    """混合搜索：关键词 + 向量

    先进行向量搜索，再在 payload 中对关键词匹配结果进行加权重排。
    """
    emb_service = get_embedding_service()
    try:
        query_vector = emb_service.generate_embedding(req.query_text, model=req.model)
    except Exception as exc:
        logger.error("生成查询向量失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"生成查询向量失败: {exc}")

    service = get_vector_search_service()
    try:
        results = service.hybrid_search(
            collection_name=req.collection,
            query_text=req.query_text,
            query_vector=query_vector,
            top_k=req.top_k,
            text_boost=req.text_boost,
        )
        return success_response(
            data={
                "results": results,
                "collection": req.collection,
                "query_text": req.query_text,
                "top_k": req.top_k,
            }
        )
    except Exception as exc:
        logger.error("混合搜索失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"混合搜索失败: {exc}")


@router.delete("/{collection}/{point_id}")
def vector_delete(
    collection: str,
    point_id: str,
    user: User = Depends(get_current_user),
):
    """删除单个向量"""
    service = get_vector_search_service()
    try:
        result = service.delete_vectors(
            collection_name=collection,
            point_ids=[point_id],
        )
        return success_response(data=result)
    except Exception as exc:
        logger.error("删除向量失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"删除向量失败: {exc}")


@router.post("/delete-batch")
def vector_delete_batch(
    req: VectorDeleteRequest,
    user: User = Depends(get_current_user),
):
    """批量删除向量"""
    service = get_vector_search_service()
    try:
        result = service.delete_vectors(
            collection_name=req.collection,
            point_ids=req.point_ids,
        )
        return success_response(data=result)
    except Exception as exc:
        logger.error("批量删除向量失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"批量删除向量失败: {exc}")


@router.get("/collections")
def vector_collections(
    user: User = Depends(get_current_user),
):
    """获取所有向量集合"""
    service = get_vector_search_service()
    try:
        collections = service.get_collections()
        return success_response(data={"collections": collections})
    except Exception as exc:
        logger.error("获取集合列表失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"获取集合列表失败: {exc}")
