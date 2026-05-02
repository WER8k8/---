from datetime import datetime
from typing import Optional
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
    resource_type: str
    resource_id: str
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