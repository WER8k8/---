# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# 新闻分类
class NewsCategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class NewsCategoryCreate(NewsCategoryBase):
    pass


class NewsCategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class NewsCategoryResponse(NewsCategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime


# 新闻文章
class NewsArticleBase(BaseModel):
    title: str
    slug: str
    content: str
    summary: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    status: str = "draft"
    is_published: bool = False
    is_active: bool = True


class NewsArticleCreate(NewsArticleBase):
    pass


class NewsArticleUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    status: Optional[str] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


class NewsArticleResponse(NewsArticleBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    view_count: int = 0
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# 批量操作请求
class BatchDeleteRequest(BaseModel):
    ids: List[str]


class BatchPublishRequest(BaseModel):
    ids: List[str]
