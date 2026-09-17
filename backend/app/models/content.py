# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import uuid
from datetime import datetime, timezone

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.orm import relationship

from app.core.database import UUID_TYPE, Base
from app.models.soft_delete import SoftDeleteMixin


class ContentPage(SoftDeleteMixin, Base):
    __tablename__ = "content_pages"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    slug = Column(String(200), nullable=False, unique=True, index=True)
    content = Column(Text)
    summary = Column(Text)
    featured_image = Column(String(500))
    page_type = Column(String(50), default="page", nullable=False)
    status = Column(String(20), default="draft", nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    author_id = Column(UUID_TYPE, ForeignKey("users.id"))
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))

    author = relationship("User")



class ContentVersion(Base):
    __tablename__ = "content_versions"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(
        UUID_TYPE,
        ForeignKey("content_pages.id"),
        nullable=False,
        index=True)
    version_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    change_note = Column(String(500))
    author_id = Column(UUID_TYPE, index=True, nullable=True)  # 添加 author_id 字段
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))

    page = relationship("ContentPage")


class ContentTemplate(Base):
    __tablename__ = "content_templates"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    # product, manufacturer, case, price
    template_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    variables = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=10)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))


class GeneratedContent(Base):
    __tablename__ = "generated_contents"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    district_id = Column(
        UUID_TYPE,
        ForeignKey("districts.id"),
        nullable=False,
        index=True)
    keyword_id = Column(
        UUID_TYPE,
        ForeignKey("generated_keywords.id"),
        nullable=False,
        index=True)
    template_id = Column(
        UUID_TYPE,
        ForeignKey("content_templates.id"),
        index=True)
    original_content = Column(Text)
    similarity_rate = Column(Float, default=0.0)
    word_count = Column(Integer, default=0)
    # draft, generated, approved, published
    status = Column(String(20), default="draft", nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))

    district = relationship("District")
    keyword = relationship("GeneratedKeyword")
    template = relationship("ContentTemplate")


class Platform(Base):
    __tablename__ = "platforms"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    # baidu, alibaba, tencent, byte, blog, b2b, forum
    platform_type = Column(String(50), nullable=False)
    icon = Column(String(200))
    base_url = Column(String(500))
    region = Column(String(20), default="cn", index=True)  # cn | global
    content_type = Column(String(30), default="article")  # article | short_video | long_video
    has_api = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))


class PlatformAccount(Base):
    __tablename__ = "platform_accounts"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, index=True)
    platform_id = Column(
        UUID_TYPE,
        ForeignKey("platforms.id"),
        nullable=False,
        index=True)
    account_name = Column(String(100), nullable=False)
    username = Column(String(100))
    email = Column(String(100))
    cookie_data = Column(Text)
    token_data = Column(JSON, default=dict)
    token_expire_at = Column(DateTime(timezone=True))
    # logged_out, logged_in, expired
    login_status = Column(String(20), default="logged_out")
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))

    platform = relationship("Platform")


class PlatformConfig(Base):
    __tablename__ = "platform_configs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    platform_id = Column(
        UUID_TYPE,
        ForeignKey("platforms.id"),
        nullable=False,
        index=True)
    account_id = Column(
        UUID_TYPE,
        ForeignKey("platform_accounts.id"),
        index=True)
    config_key = Column(String(100), nullable=False)
    config_value = Column(String(500))
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))

    platform = relationship("Platform")
    account = relationship("PlatformAccount")


class PublishTask(Base):
    __tablename__ = "publish_tasks"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    content_master_id = Column(
        UUID_TYPE,
        ForeignKey("content_masters.id"),
        nullable=True,
        index=True,
    )
    content_id = Column(
        UUID_TYPE,
        ForeignKey("generated_contents.id"),
        nullable=True,
        index=True,
    )
    region = Column(String(20), default="cn")
    primary_url = Column(String(1000))
    secondary_url = Column(String(1000))
    platform_id = Column(
        UUID_TYPE,
        ForeignKey("platforms.id"),
        nullable=False,
        index=True)
    account_id = Column(
        UUID_TYPE,
        ForeignKey("platform_accounts.id"),
        nullable=False,
        index=True)
    # pending, processing, success, failed
    status = Column(String(20), default="pending")
    # immediate, scheduled, batch
    publish_type = Column(String(20), default="immediate")
    scheduled_time = Column(DateTime(timezone=True))
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text)
    published_url = Column(String(1000))
    tenant_id = Column(String(36), nullable=True, index=True)
    utm_source = Column(String(120))
    utm_medium = Column(String(120))
    utm_campaign = Column(String(200), index=True)
    utm_content = Column(String(200))
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))
    published_at = Column(DateTime(timezone=True))
    content = relationship("GeneratedContent")
    platform = relationship("Platform")
    account = relationship("PlatformAccount")


class PublishLog(Base):
    __tablename__ = "publish_logs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(
        UUID_TYPE,
        ForeignKey("publish_tasks.id"),
        nullable=False,
        index=True)
    level = Column(String(20), nullable=False)  # info, warning, error
    message = Column(Text, nullable=False)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))

    task = relationship("PublishTask")


class InclusionStatus(Base):
    __tablename__ = "inclusion_status"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(
        UUID_TYPE,
        ForeignKey("publish_tasks.id"),
        nullable=False,
        index=True)
    url = Column(String(1000), nullable=False)
    keyword = Column(String(500))
    is_included = Column(Boolean, default=False)
    ranking = Column(Integer)
    search_engine = Column(String(50), default="baidu")
    last_checked_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))

    task = relationship("PublishTask")


class SystemSetting(Base):
    __tablename__ = "system_settings"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    setting_key = Column(String(100), nullable=False, unique=True, index=True)
    setting_value = Column(Text)
    # string, int, float, bool, json
    setting_type = Column(String(50), default="string")
    description = Column(String(500))
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))


class AIGenerationConfig(Base):
    __tablename__ = "ai_generation_configs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    config_name = Column(String(100), nullable=False)
    model_name = Column(String(100), nullable=False)
    max_tokens = Column(Integer, default=2000)
    temperature = Column(Float, default=0.7)
    creativity_level = Column(String(20),
                              default="medium")  # low, medium, high
    similarity_threshold = Column(Float, default=0.1)
    compliance_check = Column(Boolean, default=True)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))


class RiskControlConfig(Base):
    __tablename__ = "risk_control_configs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    platform_id = Column(UUID_TYPE, ForeignKey("platforms.id"), index=True)
    daily_limit = Column(Integer, default=50)
    interval_seconds = Column(Integer, default=300)
    peak_hours = Column(JSON, default=list)
    off_peak_hours = Column(JSON, default=list)
    enabled = Column(Boolean, default=True)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))

    platform = relationship("Platform")


from app.models.seo_metadata import SeoMetadata  # noqa: E402  re-export for legacy imports
