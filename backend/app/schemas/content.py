# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ContentPageCreate(BaseModel):
    title: str
    slug: str
    content: Optional[str] = None
    summary: Optional[str] = None
    page_type: Optional[str] = "page"
    status: Optional[str] = "draft"


class ContentPageUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    page_type: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class ContentPageResponse(BaseModel):
    id: str
    title: str
    slug: str
    content: Optional[str]
    summary: Optional[str]
    page_type: str
    status: str
    author_id: Optional[str]
    view_count: int
    is_active: bool
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ContentPageListResponse(BaseModel):
    items: List[ContentPageResponse]
    total: int
    page: int
    page_size: int


class ContentVersionCreate(BaseModel):
    change_note: Optional[str] = None


class ContentVersionResponse(BaseModel):
    id: str
    page_id: str
    version_number: int
    title: str
    content: Optional[str]
    summary: Optional[str]
    change_note: Optional[str]
    author_id: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class ContentRollbackRequest(BaseModel):
    version_id: str


class SeoMetadataCreate(BaseModel):
    resource_type: str
    resource_id: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    canonical_url: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    schema_markup: Optional[str] = None
    noindex: Optional[bool] = False
    h1_tag: Optional[str] = None


class SeoMetadataUpdate(BaseModel):
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    canonical_url: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    schema_markup: Optional[str] = None
    noindex: Optional[bool] = None
    h1_tag: Optional[str] = None


class SeoMetadataResponse(BaseModel):
    id: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    meta_title: Optional[str]
    meta_description: Optional[str]
    meta_keywords: Optional[str]
    canonical_url: Optional[str]
    og_title: Optional[str]
    og_description: Optional[str]
    og_image: Optional[str]
    schema_markup: Optional[str]
    noindex: bool
    h1_tag: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}
