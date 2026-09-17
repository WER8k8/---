# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
SEO Metadata API Router - SEO元数据API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.response import success_response
from app.models.seo_metadata import SEOMetadata


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/seo-metadata"
ROUTE_TAGS = ["SEO元数据"]

router = APIRouter(tags=["seo-metadata"])


@router.post("/", response_model=dict)
def create_seo_metadata(
    entity_type: str,  # product/content/page
    entity_id: str,
    meta_title: Optional[str] = None,
    meta_description: Optional[str] = None,
    meta_keywords: Optional[str] = None,
    og_title: Optional[str] = None,
    og_description: Optional[str] = None,
    og_image: Optional[str] = None,
    canonical_url: Optional[str] = None,
    hreflang_tags: Optional[str] = None,  # JSON string
    structured_data: Optional[str] = None,  # JSON string
    db: Session = Depends(get_db)
):
    """创建SEO元数据"""
    try:
        seo = SEOMetadata(
            entity_type=entity_type,
            entity_id=uuid.UUID(entity_id),
            meta_title=meta_title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            og_title=og_title,
            og_description=og_description,
            og_image=og_image,
            canonical_url=canonical_url,
            hreflang_tags=hreflang_tags,
            structured_data=structured_data,
        )
        db.add(seo)
        db.commit()
        db.refresh(seo)
        return success_response(data={"id": str(seo.id), "entity_type": seo.entity_type, "entity_id": str(seo.entity_id)})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{seo_id}", response_model=dict)
def get_seo_metadata(seo_id: str, db: Session = Depends(get_db)):
    """获取SEO元数据详情"""
    seo = db.query(SEOMetadata).filter(SEOMetadata.id == uuid.UUID(seo_id)).first()
    if not seo:
        raise HTTPException(status_code=404, detail="SEO metadata not found")
    
    return success_response(data={
        "id": str(seo.id),
        "entity_type": seo.entity_type,
        "entity_id": str(seo.entity_id),
        "meta_title": seo.meta_title,
        "meta_description": seo.meta_description,
        "meta_keywords": seo.meta_keywords,
        "og_title": seo.og_title,
        "og_description": seo.og_description,
        "og_image": seo.og_image,
        "canonical_url": seo.canonical_url,
        "hreflang_tags": seo.hreflang_tags,
        "structured_data": seo.structured_data,
    })


@router.get("/by-entity", response_model=dict)
def get_seo_by_entity(entity_type: str, entity_id: str, db: Session = Depends(get_db)):
    """根据实体类型和ID获取SEO元数据"""
    seo = db.query(SEOMetadata).filter(
        SEOMetadata.entity_type == entity_type,
        SEOMetadata.entity_id == uuid.UUID(entity_id)
    ).first()
    if not seo:
        raise HTTPException(status_code=404, detail="SEO metadata not found")
    
    return success_response(data={
        "id": str(seo.id),
        "entity_type": seo.entity_type,
        "entity_id": str(seo.entity_id),
        "meta_title": seo.meta_title,
        "meta_description": seo.meta_description,
        "og_title": seo.og_title,
        "og_description": seo.og_description,
        "og_image": seo.og_image,
        "canonical_url": seo.canonical_url,
        "hreflang_tags": seo.hreflang_tags,
        "structured_data": seo.structured_data,
    })


@router.put("/{seo_id}", response_model=dict)
def update_seo_metadata(
    seo_id: str,
    meta_title: Optional[str] = None,
    meta_description: Optional[str] = None,
    meta_keywords: Optional[str] = None,
    og_title: Optional[str] = None,
    og_description: Optional[str] = None,
    og_image: Optional[str] = None,
    canonical_url: Optional[str] = None,
    hreflang_tags: Optional[str] = None,
    structured_data: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新SEO元数据"""
    seo = db.query(SEOMetadata).filter(SEOMetadata.id == uuid.UUID(seo_id)).first()
    if not seo:
        raise HTTPException(status_code=404, detail="SEO metadata not found")
    
    if meta_title is not None:
        seo.meta_title = meta_title
    if meta_description is not None:
        seo.meta_description = meta_description
    if meta_keywords is not None:
        seo.meta_keywords = meta_keywords
    if og_title is not None:
        seo.og_title = og_title
    if og_description is not None:
        seo.og_description = og_description
    if og_image is not None:
        seo.og_image = og_image
    if canonical_url is not None:
        seo.canonical_url = canonical_url
    if hreflang_tags is not None:
        seo.hreflang_tags = hreflang_tags
    if structured_data is not None:
        seo.structured_data = structured_data
    
    db.commit()
    db.refresh(seo)
    return success_response(data={"id": str(seo.id), "entity_type": seo.entity_type, "entity_id": str(seo.entity_id)})


@router.delete("/{seo_id}")
def delete_seo_metadata(seo_id: str, db: Session = Depends(get_db)):
    """删除SEO元数据"""
    seo = db.query(SEOMetadata).filter(SEOMetadata.id == uuid.UUID(seo_id)).first()
    if not seo:
        raise HTTPException(status_code=404, detail="SEO metadata not found")
    
    db.delete(seo)
    db.commit()
    return success_response(message="SEO metadata deleted successfully")


@router.get("/", response_model=List[dict])
def list_seo_metadata(
    entity_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """列出SEO元数据（支持过滤）"""
    query = db.query(SEOMetadata)
    if entity_type:
        query = query.filter(SEOMetadata.entity_type == entity_type)
    
    seo_list = query.offset(skip).limit(limit).all()
    return [
        {
            "id": str(s.id),
            "entity_type": s.entity_type,
            "entity_id": str(s.entity_id),
            "meta_title": s.meta_title,
            "og_title": s.og_title,
        }
        for s in seo_list
    ]
