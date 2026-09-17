# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
邮件外联模型 —— 状态机 + 幂等 + 全链路追踪

状态流转：
    draft → queued → sending → sent → delivered → opened → clicked
                            ↘ bounced
                            ↘ complained
                            ↘ unsubscribed

幂等控制：同一 idempotency_key 的邮件只发送一次。
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Index, Integer,
    JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base, UUID_TYPE


class EmailStatus(str, enum.Enum):
    """邮件发送状态机"""
    DRAFT = "draft"           # 草稿
    QUEUED = "queued"         # 已入队，等待发送
    SENDING = "sending"       # 正在发送
    SENT = "sent"             # 已提交到服务商
    DELIVERED = "delivered"   # 已送达（服务商确认）
    OPENED = "opened"         # 已打开（像素追踪）
    CLICKED = "clicked"       # 已点击（链接追踪）
    BOUNCED = "bounced"       # 退回（硬退/软退）
    COMPLAINED = "complained" # 被投诉（标记为垃圾邮件）
    UNSUBSCRIBED = "unsubscribed"  # 已退订
    FAILED = "failed"         # 发送失败（可重试）
    CANCELLED = "cancelled"   # 已取消


class BounceType(str, enum.Enum):
    """退回类型"""
    HARD = "hard"     # 硬退：邮箱不存在，不再重试
    SOFT = "soft"     # 软退：临时问题，可重试


class EmailOutreach(Base):
    """邮件外联记录 —— 状态机 + 幂等 + 追踪"""
    __tablename__ = "email_outreachs"
    id = Column(UUID_TYPE, primary_key=True, default=UUID_TYPE)
    # 幂等键：同一键值只发送一次
    idempotency_key = Column(
        String(64), nullable=False, unique=True, index=True,
        comment="幂等键：同一键值只发送一次邮件",
    )
    # 租户/用户隔离
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True, index=True)
    # 发件信息
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=False, default="优丁出海")
    to_email = Column(String(255), nullable=False, index=True)
    reply_to = Column(String(255), nullable=True)
    # 邮件内容
    subject = Column(String(500), nullable=False)
    html_body = Column(Text, nullable=False)
    text_body = Column(Text, nullable=True)  # 纯文本备选
    # 状态机
    status = Column(
        Enum(EmailStatus, name="email_status_enum"),
        nullable=False,
        default=EmailStatus.DRAFT,
        index=True,
    )
    # 序列信息（Drip Campaign）
    sequence_id = Column(String(64), nullable=True, index=True)
    sequence_step = Column(Integer, nullable=True, default=0)
    sequence_total_steps = Column(Integer, nullable=True, default=0)
    # 追踪
    tracking_pixel_id = Column(String(64), nullable=True, unique=True)
    tracking_links = Column(JSON, default=dict)  # {url: tracking_id}
    # 打开/点击统计
    open_count = Column(Integer, nullable=False, default=0)
    first_opened_at = Column(DateTime(timezone=True), nullable=True)
    last_opened_at = Column(DateTime(timezone=True), nullable=True)
    click_count = Column(Integer, nullable=False, default=0)
    first_clicked_at = Column(DateTime(timezone=True), nullable=True)
    last_clicked_at = Column(DateTime(timezone=True), nullable=True)
    # 退回信息
    bounce_type = Column(Enum(BounceType, name="bounce_type_enum"), nullable=True)
    bounce_reason = Column(String(500), nullable=True)
    bounced_at = Column(DateTime(timezone=True), nullable=True)
    # 服务商信息
    provider = Column(String(32), nullable=True)  # resend / smtp / sendgrid
    provider_message_id = Column(String(255), nullable=True)
    # 元数据
    outreach_metadata = Column(JSON, default=dict)  # 额外信息：模板ID、A/B测试分组等
    tags = Column(JSON, default=list)
    # 时间戳
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    # 复合索引
    __table_args__ = (
        Index("idx_email_outreach_tenant_status", "tenant_id", "status"),
        Index("idx_email_outreach_sequence", "sequence_id", "sequence_step"),
        Index("idx_email_outreach_to_status", "to_email", "status"),
        Index("idx_email_outreach_created", "created_at"),
    )
    # ── 状态机方法 ──
    def can_transition_to(self, new_status: EmailStatus) -> bool:
        """检查状态是否允许流转到 new_status。"""
        allowed = {
            EmailStatus.DRAFT: {
                EmailStatus.QUEUED, EmailStatus.CANCELLED,
            },
            EmailStatus.QUEUED: {
                EmailStatus.SENDING, EmailStatus.CANCELLED,
            },
            EmailStatus.SENDING: {
                EmailStatus.SENT, EmailStatus.FAILED,
            },
            EmailStatus.SENT: {
                EmailStatus.DELIVERED, EmailStatus.BOUNCED,
                EmailStatus.COMPLAINED,
            },
            EmailStatus.DELIVERED: {
                EmailStatus.OPENED, EmailStatus.CLICKED,
                EmailStatus.BOUNCED, EmailStatus.COMPLAINED,
            },
            EmailStatus.OPENED: {
                EmailStatus.CLICKED, EmailStatus.BOUNCED,
                EmailStatus.COMPLAINED, EmailStatus.UNSUBSCRIBED,
            },
            EmailStatus.CLICKED: {
                EmailStatus.BOUNCED, EmailStatus.COMPLAINED,
                EmailStatus.UNSUBSCRIBED,
            },
            EmailStatus.FAILED: {
                EmailStatus.QUEUED,  # 重试
            },
        }
        return new_status in allowed.get(self.status, set())

    def transition(self, new_status: EmailStatus) -> None:
        """执行状态流转，不保存。调用方需自行 commit。"""
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"非法状态流转: {self.status.value} → {new_status.value}"
            )
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
        # 自动记录时间戳
        now = datetime.now(timezone.utc)
        if new_status == EmailStatus.SENT and not self.sent_at:
            self.sent_at = now
        elif new_status == EmailStatus.OPENED and not self.first_opened_at:
            self.first_opened_at = now
            self.last_opened_at = now
        elif new_status == EmailStatus.OPENED:
            self.last_opened_at = now
        elif new_status == EmailStatus.CLICKED and not self.first_clicked_at:
            self.first_clicked_at = now
            self.last_clicked_at = now
        elif new_status == EmailStatus.CLICKED:
            self.last_clicked_at = now
        elif new_status == EmailStatus.BOUNCED:
            self.bounced_at = now
