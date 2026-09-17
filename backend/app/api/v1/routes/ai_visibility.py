# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GEO / AI Visibility 路由 — AI 搜索可见性监控（Phase 6）。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.ai_visibility import (
    AICitation,
    AIMention,
    AIQuery,
    AIQueryRun,
    CompetitorMention,
    VisibilityScore,
)
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/geo"
ROUTE_TAGS = ["GEO可见性"]

router = APIRouter()


@router.get("/queries", summary="AI 查询问题列表")
def list_queries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出（list_queries）：处理相关业务逻辑并返回结果。

    :param page: 入参 (int)。
    :param page_size: 入参 (int)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    q = db.query(AIQuery).filter(AIQuery.deleted_at.is_(None))
    total = q.count()
    items = q.order_by(AIQuery.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    data = [{"id": str(i.id), "query": i.query, "language": i.language, "category": i.category, "target_entity": i.target_entity} for i in items]
    return success_response(data={"items": data, "total": total, "page": page, "page_size": page_size})


@router.post("/queries", summary="新增 AI 查询问题")
def create_query(body: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    创建（create_query）：处理相关业务逻辑并返回结果。

    :param body: 入参 (dict)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    q = AIQuery(
        query=str(body.get("query", "")).strip(),
        language=body.get("language") or "en",
        category=body.get("category"),
        target_entity=body.get("target_entity"),
    )
    if not q.query:
        return error_response(400, "query 必填")
    db.add(q)
    db.commit()
    db.refresh(q)
    return success_response(data={"id": str(q.id), "query": q.query}, message="查询问题已添加")


@router.post("/runs", summary="记录一次 AI 查询运行")
def create_run(body: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """记录 AI 查询结果快照：是否出现/是否被推荐/位置。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    run = AIQueryRun(
        query_id=body.get("query_id"),
        engine=body.get("engine"),
        raw_answer=body.get("raw_answer"),
        entity_appeared=str(1 if body.get("entity_appeared") else 0),
        recommended=str(1 if body.get("recommended") else 0),
        position=body.get("position"),
    )
    db.add(run)
    db.flush()
    entity = body.get("target_entity") or body.get("entity")
    if entity:
        db.add(AIMention(
            query_id=body.get("query_id"),
            run_id=run.id,
            entity=entity,
            mentioned=str(1 if body.get("entity_appeared") else 0),
            recommended=str(1 if body.get("recommended") else 0),
            snippet=body.get("snippet"),
        ))
        if body.get("cited_url"):
            db.add(AICitation(
                run_id=run.id,
                entity=entity,
                cited_url=body.get("cited_url"),
                cited_page=body.get("cited_page"),
                relevance_score=body.get("relevance_score"),
            ))
        for comp in body.get("competitors") or []:
            db.add(CompetitorMention(
                query_id=body.get("query_id"),
                run_id=run.id,
                competitor=comp.get("name", "unknown"),
                mentioned=str(1 if comp.get("appeared") else 0),
                recommended=str(1 if comp.get("recommended") else 0),
            ))
        # 更新可见性总分
        vs = db.query(VisibilityScore).filter(
            VisibilityScore.entity == entity, VisibilityScore.deleted_at.is_(None)
        ).first()
        mention_count = db.query(AIMention).filter(AIMention.entity == entity, AIMention.deleted_at.is_(None)).count()
        rec_count = db.query(AIMention).filter(
            AIMention.entity == entity, AIMention.deleted_at.is_(None), AIMention.recommended == "1"
        ).count()
        citation_count = db.query(AICitation).filter(
            AICitation.entity == entity, AICitation.deleted_at.is_(None)
        ).count()
        if not vs:
            vs = VisibilityScore(entity=entity)
            db.add(vs)
        vs.mention_count = mention_count
        vs.recommendation_count = rec_count
        vs.citation_count = citation_count
        vs.query_coverage = db.query(AIQuery).filter(AIQuery.deleted_at.is_(None)).count()
        # Mention 40 + Recommendation 30 + Citation 20 + Coverage 10，封顶 100
        vs.score = min(
            100,
            int(40 * (1 if mention_count else 0) / 1)
            + int(30 * (1 if rec_count else 0) / 1)
            + min(20, citation_count * 5)
            + min(10, vs.query_coverage),
        )
        vs.computed_at = datetime.now(timezone.utc)
    db.commit()
    return success_response(data={"id": str(run.id)}, message="运行已记录")


@router.get("/visibility", summary="GEO 可见性得分")
def list_visibility(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出（list_visibility）：处理相关业务逻辑并返回结果。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    items = db.query(VisibilityScore).filter(VisibilityScore.deleted_at.is_(None)).order_by(VisibilityScore.score.desc()).all()
    return success_response(data=[{
        "entity": v.entity,
        "score": v.score,
        "mention_count": v.mention_count,
        "recommendation_count": v.recommendation_count,
        "citation_count": v.citation_count,
        "query_coverage": v.query_coverage,
        "computed_at": v.computed_at.isoformat() if v.computed_at else None,
    } for v in items])
