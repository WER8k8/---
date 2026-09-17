# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国际询盘采集系统 Schema"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ===== 目标网站 =====

class InternationalTargetSiteCreate(BaseModel):
    name: str
    url: str
    region: str
    language: str = "en"
    crawl_interval: int = 60
    status: str = "active"


class InternationalTargetSiteUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    region: Optional[str] = None
    language: Optional[str] = None
    crawl_interval: Optional[int] = None
    status: Optional[str] = None


class InternationalTargetSiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    url: str
    region: str
    language: str
    crawl_interval: int
    last_crawled_at: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime


# ===== 询盘 =====

class InternationalInquiryUpdate(BaseModel):
    status: Optional[str] = None
    customer_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None   # 跟进备注


class InternationalInquiryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    source_site_id: Optional[str] = None
    source_url: str
    source_title: Optional[str] = None
    customer_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    company: Optional[str] = None
    product_interest: Optional[str] = None
    product_model: Optional[str] = None
    quantity: Optional[str] = None
    budget: Optional[str] = None
    message: Optional[str] = None
    inquiry_time: Optional[str] = None
    crawled_at: Optional[datetime] = None
    language: Optional[str] = None
    region: Optional[str] = None
    confidence: int = 0
    status: str = "pending"
    created_at: datetime
    updated_at: datetime


# ===== 统计 =====

class InternationalStats(BaseModel):
    total_inquiries: int = 0
    today_inquiries: int = 0
    this_week_inquiries: int = 0
    pending_count: int = 0
    by_region: list = []
    by_status: list = []
