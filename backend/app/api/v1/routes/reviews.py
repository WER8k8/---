# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""评价反馈API路由"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.response import APIResponse, error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.review import Review
from app.models.user import User
from app.models.product import Product


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/reviews"
ROUTE_TAGS = ["评价反馈"]

router = APIRouter(tags=["评价反馈"])


class ReviewCreate(BaseModel):
    """创建评价请求模型"""
    product_id: str = Field(..., description="产品ID")
    rating: float = Field(..., ge=1, le=5, description="评分(1-5)")
    content: Optional[str] = Field(None, description="评价内容")
    images: Optional[List[str]] = Field(None, description="评价图片URL列表")


class ReviewUpdate(BaseModel):
    """更新评价请求模型"""
    rating: Optional[float] = Field(None, ge=1, le=5, description="评分(1-5)")
    content: Optional[str] = Field(None, description="评价内容")
    images: Optional[List[str]] = Field(None, description="评价图片URL列表")
    status: Optional[str] = Field(None, description="状态: pending, approved, rejected")


class ReviewResponse(BaseModel):
    """评价响应模型"""
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    product_id: str
    rating: float
    content: Optional[str]
    images: Optional[str]
    status: str
    created_at: str
    updated_at: str


class ReviewStatsResponse(BaseModel):
    """评价统计响应模型"""
    total_reviews: int
    average_rating: float
    rating_distribution: dict  # {1: count, 2: count, 3: count, 4: count, 5: count}


@router.post("", response_model=APIResponse[ReviewResponse])
async def create_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建评价"""
    # 检查产品是否存在
    product = db.query(Product).filter(Product.id == review_data.product_id).first()
    if not product:
        return error_response(404, "产品不存在")
    
    # 检查用户是否已经评价过该产品
    existing_review = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.product_id == review_data.product_id
    ).first()
    if existing_review:
        return error_response(400, "您已经评价过该产品")
    
    # 创建评价
    import json
    review = Review(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        product_id=review_data.product_id,
        rating=review_data.rating,
        content=review_data.content,
        images=json.dumps(review_data.images) if review_data.images else None,
        status="pending"  # 初始状态为待审核
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return success_response(
        data=ReviewResponse(
            id=str(review.id),
            user_id=str(review.user_id),
            product_id=str(review.product_id),
            rating=review.rating,
            content=review.content,
            images=review.images,
            status=review.status,
            created_at=review.created_at.isoformat() if review.created_at else "",
            updated_at=review.updated_at.isoformat() if review.updated_at else ""
        ),
        message="评价创建成功"
    )


@router.get("", response_model=APIResponse[List[ReviewResponse]])
async def get_reviews(
    product_id: Optional[str] = Query(None, description="产品ID"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    status: Optional[str] = Query(None, description="状态过滤"),
    min_rating: Optional[float] = Query(None, ge=1, le=5, description="最低评分"),
    max_rating: Optional[float] = Query(None, ge=1, le=5, description="最高评分"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取评价列表"""
    query = db.query(Review)
    # 应用过滤条件
    if product_id:
        query = query.filter(Review.product_id == product_id)
    if user_id:
        query = query.filter(Review.user_id == user_id)
    if status:
        query = query.filter(Review.status == status)
    if min_rating is not None:
        query = query.filter(Review.rating >= min_rating)
    if max_rating is not None:
        query = query.filter(Review.rating <= max_rating)
    
    # 计算总数
    total = query.count()
    # 分页
    reviews = query.order_by(Review.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    # 构建响应
    review_responses = []
    for review in reviews:
        review_responses.append(ReviewResponse(
            id=str(review.id),
            user_id=str(review.user_id),
            product_id=str(review.product_id),
            rating=review.rating,
            content=review.content,
            images=review.images,
            status=review.status,
            created_at=review.created_at.isoformat() if review.created_at else "",
            updated_at=review.updated_at.isoformat() if review.updated_at else ""
        ))
    
    return success_response(
        data=review_responses,
        message="获取评价列表成功",
        meta={
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    )


@router.get("/{review_id}", response_model=APIResponse[ReviewResponse])
async def get_review(
    review_id: str,
    db: Session = Depends(get_db)
):
    """获取单个评价详情"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        return error_response(404, "评价不存在")
    
    return success_response(
        data=ReviewResponse(
            id=str(review.id),
            user_id=str(review.user_id),
            product_id=str(review.product_id),
            rating=review.rating,
            content=review.content,
            images=review.images,
            status=review.status,
            created_at=review.created_at.isoformat() if review.created_at else "",
            updated_at=review.updated_at.isoformat() if review.updated_at else ""
        ),
        message="获取评价详情成功"
    )


@router.put("/{review_id}", response_model=APIResponse[ReviewResponse])
async def update_review(
    review_id: str,
    review_data: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新评价（用户只能更新自己的评价，管理员可以更新任何评价）"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        return error_response(404, "评价不存在")
    
    # 检查权限：用户只能更新自己的评价，管理员可以更新任何评价
    if review.user_id != current_user.id and current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")
    
    # 更新评价
    import json
    if review_data.rating is not None:
        review.rating = review_data.rating
    if review_data.content is not None:
        review.content = review_data.content
    if review_data.images is not None:
        review.images = json.dumps(review_data.images)
    if review_data.status is not None and current_user.role in ["admin", "super_admin"]:
        review.status = review_data.status
    
    db.commit()
    db.refresh(review)
    return success_response(
        data=ReviewResponse(
            id=str(review.id),
            user_id=str(review.user_id),
            product_id=str(review.product_id),
            rating=review.rating,
            content=review.content,
            images=review.images,
            status=review.status,
            created_at=review.created_at.isoformat() if review.created_at else "",
            updated_at=review.updated_at.isoformat() if review.updated_at else ""
        ),
        message="评价更新成功"
    )


@router.delete("/{review_id}", response_model=APIResponse)
async def delete_review(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除评价（用户只能删除自己的评价，管理员可以删除任何评价）"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        return error_response(404, "评价不存在")
    
    # 检查权限：用户只能删除自己的评价，管理员可以删除任何评价
    if review.user_id != current_user.id and current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")
    
    db.delete(review)
    db.commit()
    return success_response(message="评价删除成功")


@router.put("/{review_id}/approve", response_model=APIResponse[ReviewResponse])
async def approve_review(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """审核通过评价（管理员功能）"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")
    
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        return error_response(404, "评价不存在")
    
    review.status = "approved"
    db.commit()
    db.refresh(review)
    return success_response(
        data=ReviewResponse(
            id=str(review.id),
            user_id=str(review.user_id),
            product_id=str(review.product_id),
            rating=review.rating,
            content=review.content,
            images=review.images,
            status=review.status,
            created_at=review.created_at.isoformat() if review.created_at else "",
            updated_at=review.updated_at.isoformat() if review.updated_at else ""
        ),
        message="评价审核通过"
    )


@router.put("/{review_id}/reject", response_model=APIResponse[ReviewResponse])
async def reject_review(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """审核拒绝评价（管理员功能）"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")
    
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        return error_response(404, "评价不存在")
    
    review.status = "rejected"
    db.commit()
    db.refresh(review)
    return success_response(
        data=ReviewResponse(
            id=str(review.id),
            user_id=str(review.user_id),
            product_id=str(review.product_id),
            rating=review.rating,
            content=review.content,
            images=review.images,
            status=review.status,
            created_at=review.created_at.isoformat() if review.created_at else "",
            updated_at=review.updated_at.isoformat() if review.updated_at else ""
        ),
        message="评价审核拒绝"
    )


@router.get("/stats", response_model=APIResponse[ReviewStatsResponse])
async def get_review_stats(
    product_id: Optional[str] = Query(None, description="产品ID"),
    db: Session = Depends(get_db)
):
    """获取评价统计信息"""
    query = db.query(Review)
    # 如果指定了产品ID，只统计该产品的评价
    if product_id:
        query = query.filter(Review.product_id == product_id)
    
    # 只统计已审核通过的评价
    query = query.filter(Review.status == "approved")
    # 计算总数
    total_reviews = query.count()
    if total_reviews == 0:
        return success_response(
            data=ReviewStatsResponse(
                total_reviews=0,
                average_rating=0.0,
                rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            ),
            message="暂无评价数据"
        )
    
    # 计算平均评分
    from sqlalchemy import func
    average_rating = db.query(func.avg(Review.rating)).filter(
        Review.status == "approved",
        Review.product_id == product_id if product_id else True
    ).scalar() or 0.0
    # 计算评分分布
    rating_distribution = {}
    for rating in [1, 2, 3, 4, 5]:
        count = query.filter(Review.rating == rating).count()
        rating_distribution[rating] = count
    
    return success_response(
        data=ReviewStatsResponse(
            total_reviews=total_reviews,
            average_rating=round(average_rating, 1),
            rating_distribution=rating_distribution
        ),
        message="获取评价统计成功"
    )


@router.get("/products/{product_id}/reviews", response_model=APIResponse[List[ReviewResponse]])
async def get_product_reviews(
    product_id: str,
    status: Optional[str] = Query("approved", description="状态过滤（默认只显示已审核通过的）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取指定产品的评价列表（前端展示使用）"""
    # 检查产品是否存在
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return error_response(404, "产品不存在")
    
    # 构建查询
    query = db.query(Review).filter(Review.product_id == product_id)
    # 默认只显示已审核通过的评价
    if status:
        query = query.filter(Review.status == status)
    else:
        query = query.filter(Review.status == "approved")
    
    # 计算总数
    total = query.count()
    # 分页
    reviews = query.order_by(Review.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    # 构建响应
    review_responses = []
    for review in reviews:
        review_responses.append(ReviewResponse(
            id=str(review.id),
            user_id=str(review.user_id),
            product_id=str(review.product_id),
            rating=review.rating,
            content=review.content,
            images=review.images,
            status=review.status,
            created_at=review.created_at.isoformat() if review.created_at else "",
            updated_at=review.updated_at.isoformat() if review.updated_at else ""
        ))
    
    return success_response(
        data=review_responses,
        message="获取产品评价列表成功",
        meta={
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    )
