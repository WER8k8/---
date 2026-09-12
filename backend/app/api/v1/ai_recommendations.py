"""
AI Recommendations API Router - AI推荐API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.models.ai_recommendation import AIRecommendation


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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
def get_recommendation(recommendation_id: str, db: Session = Depends(get_db)):
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
def delete_recommendation(recommendation_id: str, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
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
