# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""社媒互动（评论/私信）— 自动谈单状态机落库。"""

from __future__ import annotations

import uuid as _uuid_lib

from sqlalchemy import Column, DateTime, String, Text, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class SocialInteraction(Base):
    """抖音等平台评论/私信 → 意向识别 → 谈单草稿 → 发送回执。"""
    __tablename__ = "social_interactions"
    id = Column(String(36), primary_key=True, default=lambda: str(_uuid_lib.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    platform = Column(String(32), nullable=False, default="douyin", index=True)
    interaction_type = Column(String(16), nullable=False, default="comment")  # comment | dm
    platform_post_id = Column(String(128), nullable=True, index=True)
    platform_comment_id = Column(String(128), nullable=True, index=True)
    author_name = Column(String(120), nullable=False, default="访客")
    author_platform_id = Column(String(128), nullable=True)
    content = Column(Text, nullable=False)
    intent = Column(String(32), nullable=False, default="general")  # inquiry | price | general | spam
    status = Column(String(20), nullable=False, default="pending", index=True)
    # pending → draft_ready → approved → sent | failed | skipped
    draft_reply = Column(Text, nullable=True)
    final_reply = Column(Text, nullable=True)
    platform_send_receipt = Column(JSON, nullable=True)
    inquiry_id = Column(String(36), nullable=True, index=True)
    error_code = Column(String(64), nullable=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    def __repr__(self) -> str:
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<SocialInteraction platform={self.platform} status={self.status}>"
