# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
关键词排名API - Phase 4
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.seo import Keyword, KeywordRanking, SiteAudit
from app.services.keyword_tracker import DEFAULT_KEYWORDS, KeywordTracker

router = APIRouter(prefix="/keywords", tags=["关键词排名"])


def _empty_summary() -> dict:
    """_empty_summary。
    :return: 返回处理结果。
    """
    return {
        "total_keywords": 0,
        "top_10": 0,
        "top_50": 0,
        "improved": 0,
        "declined": 0,
        "avg_position": 0,
    }


# ==================== Pydantic Schemas ====================


class KeywordCreate(BaseModel):
    """创建关键词"""
    keyword: str = Field(..., min_length=1, max_length=200, description="关键词")
    search_engine: str = Field(default="baidu", description="搜索引擎")
    target_url: str = Field(default="", description="目标URL")
    search_volume: int = Field(default=0, description="搜索量")
    difficulty: str = Field(default="medium", description="难度")
    category: str = Field(default="", description="分类")
    notes: str = Field(default="", description="备注")


class KeywordUpdate(BaseModel):
    """更新关键词"""
    keyword: Optional[str] = None
    target_url: Optional[str] = None
    search_volume: Optional[int] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    is_tracking: Optional[bool] = None
    notes: Optional[str] = None


class KeywordResponse(BaseModel):
    """关键词响应"""
    model_config = ConfigDict(from_attributes=True)
    id: str
    keyword: str
    search_engine: str
    target_url: str
    current_position: Optional[int]
    previous_position: Optional[int]
    best_position: Optional[int]
    search_volume: int
    difficulty: str
    cpc: float
    is_tracking: bool
    category: str
    notes: str
    created_at: datetime
    updated_at: datetime
    last_checked_at: Optional[datetime]


class RankingHistoryResponse(BaseModel):
    """排名历史响应"""
    date: str
    position: Optional[int]


class TrackKeywordsRequest(BaseModel):
    """追踪关键词请求"""
    keywords: List[str] = Field(...,
                                min_length=1,
                                max_length=100,
                                description="关键词列表")
    search_engine: str = Field(default="baidu", description="搜索引擎")


class TrackKeywordsResponse(BaseModel):
    """追踪关键词响应"""
    total: int
    results: List[dict]


@router.get("/dashboard/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """获取关键词仪表盘摘要"""
    total_keywords = db.query(KeywordRanking).filter(
        KeywordRanking.is_tracking).count()

    if total_keywords == 0:
        return _empty_summary()

    top_10 = (
        db.query(KeywordRanking)
        .filter(
            KeywordRanking.is_tracking,
            KeywordRanking.current_position >= 1,
            KeywordRanking.current_position <= 10,
        )
        .count()
    )
    top_50 = (
        db.query(KeywordRanking)
        .filter(
            KeywordRanking.is_tracking,
            KeywordRanking.current_position >= 1,
            KeywordRanking.current_position <= 50,
        )
        .count()
    )
    improved = (
        db.query(KeywordRanking)
        .filter(
            KeywordRanking.is_tracking,
            KeywordRanking.previous_position.isnot(None),
            KeywordRanking.current_position < KeywordRanking.previous_position,
        )
        .count()
    )
    declined = (
        db.query(KeywordRanking)
        .filter(
            KeywordRanking.is_tracking,
            KeywordRanking.previous_position.isnot(None),
            KeywordRanking.current_position > KeywordRanking.previous_position,
        )
        .count()
    )
    avg_position = (
        db.query(func.avg(KeywordRanking.current_position))
        .filter(
            KeywordRanking.is_tracking,
            KeywordRanking.current_position.isnot(None),
        )
        .scalar() or 0
    )
    return {
        "total_keywords": total_keywords,
        "top_10": top_10,
        "top_50": top_50,
        "improved": improved,
        "declined": declined,
        "avg_position": round(float(avg_position), 2),
    }


@router.get("/", response_model=List[KeywordResponse])
async def list_keywords(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search_engine: Optional[str] = None,
    category: Optional[str] = None,
    is_tracking: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取关键词列表：优先数据库；生产无记录时返回空列表（禁止演示数据冒充）"""
    query = db.query(KeywordRanking)
    if search_engine:
        query = query.filter(KeywordRanking.search_engine == search_engine)
    if category:
        query = query.filter(KeywordRanking.category.contains(category))
    if is_tracking is not None:
        query = query.filter(KeywordRanking.is_tracking == is_tracking)

    rows = (
        query.order_by(KeywordRanking.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    if rows:
        return rows

    return []


@router.post("/", response_model=KeywordResponse, status_code=201)
async def create_keyword(
        keyword_data: KeywordCreate,
        db: Session = Depends(get_db)):
    """创建关键词"""
    # 检查是否已存在
    existing = (
        db.query(KeywordRanking) .filter(
            KeywordRanking.keyword == keyword_data.keyword,
            KeywordRanking.search_engine == keyword_data.search_engine) .first())

    if existing:
        raise HTTPException(status_code=400, detail="关键词已存在")

    keyword = KeywordRanking(**keyword_data.dict())
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.put("/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(
        keyword_id: str,
        keyword_data: KeywordUpdate,
        db: Session = Depends(get_db)):
    """更新关键词"""
    keyword = db.query(KeywordRanking).filter(
        KeywordRanking.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    update_data = keyword_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(keyword, field, value)

    db.commit()
    db.refresh(keyword)
    return keyword


@router.delete("/{keyword_id}")
async def delete_keyword(keyword_id: str, db: Session = Depends(get_db)):
    """删除关键词"""
    keyword = db.query(KeywordRanking).filter(
        KeywordRanking.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    db.delete(keyword)
    db.commit()
    return {"message": "删除成功"}


@router.post("/track", response_model=TrackKeywordsResponse)
async def track_keywords(
        request: TrackKeywordsRequest,
        db: Session = Depends(get_db)):
    """追踪关键词排名"""
    tracker = KeywordTracker(db)
    results = await tracker.track_keywords(keywords=request.keywords, search_engine=request.search_engine)
    return TrackKeywordsResponse(total=len(results), results=results)


@router.get("/{keyword_id}/history",
            response_model=List[RankingHistoryResponse])
async def get_keyword_history(
        keyword_id: str,
        days: int = Query(
            30,
            ge=1,
            le=365),
        db: Session = Depends(get_db)):
    """获取关键词排名历史"""
    keyword = db.query(KeywordRanking).filter(
        KeywordRanking.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    tracker = KeywordTracker(db)
    history = tracker.get_ranking_trend(keyword.keyword, days)
    return history


@router.post("/batch-import-defaults")
async def import_default_keywords(db: Session = Depends(get_db)):
    """导入默认关键词列表（大城保温建材产业带）。"""
    from app.services.dacheng_keyword_seed_service import seed_ranking_keywords
    result = seed_ranking_keywords(db)
    imported = int(result.get("imported") or 0)
    return {
        "message": f"成功导入 {imported} 个关键词（大城产业带）",
        "imported": imported,
        "skipped": result.get("skipped", 0),
    }
