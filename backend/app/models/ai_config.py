# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import UUID_TYPE, Base
from app.core.field_crypto import encrypt_field, decrypt_field


class TenantAiProviderConfig(Base):
    """租户级 AI 模型配置表"""
    __tablename__ = "tenant_ai_provider_configs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    provider_id = Column(String(50), nullable=False, index=True)
    protocol = Column(String(30), nullable=False, default="openai_compatible")
    model_name = Column(String(100), nullable=False)
    base_url = Column(String(300))
    api_key_encrypted = Column(Text)
    enabled = Column(Boolean, default=False, nullable=False)
    temperature = Column(String(10), default="0.1")
    scopes = Column(JSON, default=list)
    test_status = Column(String(20), default="pending")
    last_test_time = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AIModelProvider(Base):
    """AI模型提供商配置表"""
    __tablename__ = "ai_model_providers"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False, index=True)
    # openai, anthropic, gemini, nvidia, deepseek, mimo
    provider_type = Column(String(30), nullable=False, index=True)
    api_key_encrypted = Column("api_key", String(500), nullable=False)  # AES-256-GCM 加密存储
    base_url = Column(String(255))
    default_model = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    description = Column(Text)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    @property
    def api_key(self) -> str:
        """读取时自动解密"""
        return decrypt_field(self.api_key_encrypted)

    @api_key.setter
    def api_key(self, value: str):
        """写入时自动加密"""
        self.api_key_encrypted = encrypt_field(value)


class AIModelConfig(Base):
    """AI模型配置表"""
    __tablename__ = "ai_model_configs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(UUID_TYPE, nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    # code, logic, general, chinese, vision
    model_type = Column(String(30), nullable=False, index=True)
    temperature = Column(String(10), default="0.7")
    max_tokens = Column(String(10), default="4096")
    context_window = Column(String(10))
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False, index=True)
    model_metadata = Column(JSON, default=dict)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class CCSwitchConfig(Base):
    """CC Haha / CC Switch 中转配置"""
    __tablename__ = "cc_switch_configs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    provider_type = Column(
        String(30), nullable=False, default="cc_switch", index=True
    )
    base_url = Column(String(300), nullable=False)
    api_key_encrypted = Column(Text)
    model_mapping = Column(JSON, default=dict)
    rate_limit = Column(String(10), default="60")
    rate_window_seconds = Column(String(10), default="60")
    max_retries = Column(String(10), default="3")
    timeout_seconds = Column(String(10), default="30")
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    health_check_url = Column(String(300))
    last_health_status = Column(String(20))
    last_health_check_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AIUsageLog(Base):
    """AI使用日志表"""
    __tablename__ = "ai_usage_logs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(UUID_TYPE, nullable=False, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    task_type = Column(String(50), nullable=False, index=True)
    # 注意：DB 实际列类型为 varchar（写入端 ai_config_service 主动 str()），
    # 模型必须对齐 String，否则 PG 上 SELECT 整行会因 result processor 类型不匹配 500。
    prompt_tokens = Column(String(50), default="0")
    completion_tokens = Column(String(50), default="0")
    total_tokens = Column(String(50), default="0")
    cost = Column(String(50), default="0")
    duration_ms = Column(String(50), default="0")
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), nullable=False, index=True)
