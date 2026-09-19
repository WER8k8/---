# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
AI Recommendations API Router - AI推荐API
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import get_current_user
from app.models.ai_recommendation import AIRecommendation
from app.models.inquiry import Inquiry
from app.models.user import User
from app.services.ai_recommendation_service import recommendation_service


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/ai-recommendations"
ROUTE_TAGS = ["AI推荐"]

router = APIRouter(tags=["ai-recommendations"])


@router.post("/", response_model=dict)
def create_ai_recommendation(
    user_id: str,
    product_id: str,
    score: float,  # 0-1
    reason: Optional[str] = None,
    algorithm: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建AI推荐记录"""
    try:
        recommendation = AIRecommendation(
            user_id=uuid.UUID(user_id),
            product_id=uuid.UUID(product_id),
            score=score,
            reason=reason,
            algorithm=algorithm,
        )
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)
        return {"id": str(recommendation.id), "score": float(recommendation.score), "product_id": str(recommendation.product_id)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/for-user/{user_id}", response_model=List[dict])
def get_recommendations_for_user(
    user_id: str,
    algorithm: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户的推荐产品列表"""
    query = db.query(AIRecommendation).filter(AIRecommendation.user_id == uuid.UUID(user_id))
    if algorithm:
        query = query.filter(AIRecommendation.algorithm == algorithm)
    
    recommendations = query.order_by(AIRecommendation.score.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "product_id": str(r.product_id),
            "score": float(r.score),
            "reason": r.reason,
            "algorithm": r.algorithm,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recommendations
    ]


@router.get("/{recommendation_id}", response_model=dict)
def get_recommendation(recommendation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取推荐记录详情"""
    recommendation = db.query(AIRecommendation).filter(AIRecommendation.id == uuid.UUID(recommendation_id)).first()
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    return {
        "id": str(recommendation.id),
        "user_id": str(recommendation.user_id),
        "product_id": str(recommendation.product_id),
        "score": float(recommendation.score),
        "reason": recommendation.reason,
        "algorithm": recommendation.algorithm,
        "created_at": recommendation.created_at.isoformat() if recommendation.created_at else None,
    }


@router.delete("/{recommendation_id}")
def delete_recommendation(recommendation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除推荐记录"""
    recommendation = db.query(AIRecommendation).filter(AIRecommendation.id == uuid.UUID(recommendation_id)).first()
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    db.delete(recommendation)
    db.commit()
    return {"message": "Recommendation deleted successfully"}


@router.get("/", response_model=List[dict])
def list_recommendations(
    user_id: Optional[str] = None,
    product_id: Optional[str] = None,
    algorithm: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出推荐记录（支持过滤）"""
    query = db.query(AIRecommendation)
    if user_id:
        query = query.filter(AIRecommendation.user_id == uuid.UUID(user_id))
    if product_id:
        query = query.filter(AIRecommendation.product_id == uuid.UUID(product_id))
    if algorithm:
        query = query.filter(AIRecommendation.algorithm == algorithm)
    
    recommendations = query.order_by(AIRecommendation.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "user_id": str(r.user_id),
            "product_id": str(r.product_id),
            "score": float(r.score),
            "algorithm": r.algorithm,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recommendations
    ]


@router.get("/cross-sell", response_model=List[dict])
def cross_sell_recommendations(
    tenant_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """基于询盘历史的增购/交叉销售实时推荐（P1-2 接线）。

    激活 ai_recommendation_service.RecommendationService 的 item-based 协同过滤：
    以「租户 -> 询盘商品（近因加权）」构建 user_item_matrix，为目标租户返回
    与其历史询盘商品高共现、但自身尚未询盘过的商品，作为交叉销售线索。
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    rows = (
        db.query(Inquiry.tenant_id, Inquiry.product, Inquiry.created_at)
        .filter(Inquiry.product.isnot(None), Inquiry.created_at >= cutoff)
        .all()
    )
    matrix: dict[str, dict[str, float]] = {}
    now = datetime.now(timezone.utc)
    for tid, prod, created in rows:
        if not tid or not prod or created is None:
            continue
        # created_at 落库后可能为 naive（同 churn_service 的时区坑），
        # 与 tz-aware 的 now 相减会抛 TypeError，先规整为 UTC aware。
        created_aware = (
            created if created.tzinfo is not None else created.replace(tzinfo=timezone.utc)
        )
        age_days = max((now - created_aware).days, 0)
        weight = 1.0 / (1.0 + age_days / 30.0)  # 近因加权：越近权重越高
        matrix.setdefault(tid, {})
        matrix[tid][prod] = matrix[tid].get(prod, 0.0) + weight

    if tenant_id not in matrix:
        return success_response(data=[])

    recs = recommendation_service.collaborative_filtering_item_based(
        tenant_id, matrix, n_recommendations=limit
    )
    data = [{"product": p, "score": round(float(s), 4)} for p, s in recs]
    return success_response(data=data)
