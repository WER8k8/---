# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CaseImageCreate(BaseModel):
    image_url: str
    image_alt: Optional[str] = None
    sort_order: Optional[int] = 0


class CaseImageResponse(BaseModel):
    id: str
    case_id: str
    image_url: str
    image_alt: Optional[str]
    sort_order: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class CaseStudyCreate(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    client: Optional[str] = None
    location: Optional[str] = None
    is_published: bool = False


class CaseStudyUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    client: Optional[str] = None
    location: Optional[str] = None
    is_published: Optional[bool] = None


class CaseStudyResponse(BaseModel):
    id: str
    product_id: Optional[str]
    project_name: str
    slug: str
    client_name: Optional[str]
    materials_used: Optional[str]
    construction_area: Optional[str]
    project_date: Optional[str]
    location: Optional[str]
    project_address: Optional[str]
    description: Optional[str]
    cover_image: Optional[str]
    status: str
    sort_order: int
    view_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CaseStudyDetailResponse(CaseStudyResponse):
    images: List[CaseImageResponse] = []


class CaseStudyListResponse(BaseModel):
    items: List[CaseStudyResponse]
    total: int
    page: int
    page_size: int


class BatchDeleteRequest(BaseModel):
    ids: List[str]


class BatchUpdateStatusRequest(BaseModel):
    ids: List[str]
    status: str
