# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""持久化养号周期 + 平台养号规则模板（从 AiToEarn 互动管理模型合并）。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text

from app.core.database import UUID_TYPE, Base


class NurtureCycle(Base):
    """单账号养号周期（持久化，重启不丢失）。"""
    __tablename__ = "nurture_cycles"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    platform = Column(String(32), nullable=False, index=True)
    account_label = Column(String(120), nullable=False)
    platform_account_id = Column(UUID_TYPE, ForeignKey("platform_accounts.id"), nullable=True, index=True)
    # 状态机: draft → warming → active → cooling → paused → archived
    status = Column(String(20), nullable=False, default="draft", index=True)
    # 养号规则（JSON）
    rules = Column(JSON, nullable=True)
    # 例: {"warmup_days": 14, "daily_posts": 2, "daily_likes": 30, "daily_comments": 5, "daily_follows": 10}
    # 当前进度
    current_day = Column(Integer, nullable=False, default=0)
    total_posts = Column(Integer, nullable=False, default=0)
    total_likes = Column(Integer, nullable=False, default=0)
    total_comments = Column(Integer, nullable=False, default=0)
    total_follows = Column(Integer, nullable=False, default=0)
    # 频控：最近一次操作时间
    last_post_at = Column(DateTime(timezone=True), nullable=True)
    last_like_at = Column(DateTime(timezone=True), nullable=True)
    last_comment_at = Column(DateTime(timezone=True), nullable=True)
    last_follow_at = Column(DateTime(timezone=True), nullable=True)
    # 违规/风控
    warning_count = Column(Integer, nullable=False, default=0)
    cooldown_until = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class ScheduledPublish(Base):
    """定时发布任务（借鉴 AiToEarn enqueue-publishing-task scheduler）。"""
    __tablename__ = "scheduled_publishes"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    platform_account_id = Column(UUID_TYPE, ForeignKey("platform_accounts.id"), nullable=True, index=True)
    platform_name = Column(String(64), nullable=False, index=True)
    # 内容
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=True)
    video_url = Column(String(1000), nullable=True)
    cover_url = Column(String(1000), nullable=True)
    tags = Column(JSON, nullable=True)  # list[str]
    content_master_id = Column(UUID_TYPE, nullable=True)
    # 调度
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    # pending → dispatched → published | failed | cancelled
    # 执行结果
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    published_url = Column(String(1000), nullable=True)
    published_post_id = Column(String(200), nullable=True)
    error_message = Column(Text, nullable=True)
    worker_chain = Column(JSON, nullable=True)  # 实际使用的发布链路
    # 关联
    publish_task_id = Column(UUID_TYPE, ForeignKey("publish_tasks.id"), nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class EngagementRecord(Base):
    """互动记录（借鉴 AiToEngagement：评论互动/点赞/关注/自动回复）。"""
    __tablename__ = "engagement_records"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    platform = Column(String(32), nullable=False, index=True)
    platform_account_id = Column(UUID_TYPE, ForeignKey("platform_accounts.id"), nullable=True, index=True)
    # 互动类型: like | comment | follow | reply | share
    action_type = Column(String(20), nullable=False, index=True)
    target_post_id = Column(String(200), nullable=True, index=True)
    target_post_url = Column(String(1000), nullable=True)
    target_author = Column(String(200), nullable=True)
    target_comment_id = Column(String(200), nullable=True)
    # 互动内容（评论/回复时有值）
    content = Column(Text, nullable=True)
    # 状态: pending → success → failed
    status = Column(String(20), nullable=False, default="pending", index=True)
    error_message = Column(Text, nullable=True)
    # 归因到养号周期
    nurture_cycle_id = Column(UUID_TYPE, ForeignKey("nurture_cycles.id"), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
