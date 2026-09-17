# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国际询盘采集系统 - 独立于国内业务的数据库模型"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import UUID_TYPE, Base


class InternationalTargetSite(Base):
    """目标采集网站配置"""
    __tablename__ = "international_target_sites"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    region = Column(String(10), nullable=False, index=True)      # US/DE/FR/JP 等
    language = Column(String(10), default="en")
    crawl_interval = Column(Integer, default=60)                  # 采集间隔（分钟）
    last_crawled_at = Column(DateTime(timezone=True))
    status = Column(String(20), default="active", index=True)     # active/paused
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class InternationalInquiry(Base):
    """采集到的国外客户询盘"""
    __tablename__ = "international_inquiries"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_site_id = Column(UUID_TYPE, ForeignKey("international_target_sites.id"), index=True)
    source_url = Column(String(1000), nullable=False)
    source_title = Column(String(500))
    customer_name = Column(String(200), index=True)
    email = Column(String(200), index=True)
    phone = Column(String(100))
    wechat = Column(String(100))
    company = Column(String(300))
    product_interest = Column(String(500), index=True)
    product_model = Column(String(200))
    quantity = Column(String(200))
    budget = Column(String(200))
    message = Column(Text)
    inquiry_time = Column(String(100))
    crawled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    language = Column(String(10), index=True)
    region = Column(String(10), index=True)
    confidence = Column(Integer, default=0)    # 提取置信度 0-100
    raw_data = Column(Text)                    # 原始提取JSON
    status = Column(String(20), default="pending", index=True)  # pending/contacted/converted/closed
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class InternationalCrawlLog(Base):
    """采集日志"""
    __tablename__ = "international_crawl_logs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(UUID_TYPE, ForeignKey("international_target_sites.id"), index=True)
    status = Column(String(20), default="success", index=True)   # success/failed
    pages_crawled = Column(Integer, default=0)
    inquiries_found = Column(Integer, default=0)
    error_message = Column(Text)
    duration_seconds = Column(Integer, default=0)
    ip_used = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
