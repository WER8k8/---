# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Inquiry Model - 询盘模型
买家向商家发起的询盘（询价请求）
"""
import uuid as _uuid_lib

from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base, UUID_TYPE
from app.models.soft_delete import SoftDeleteMixin


class Inquiry(SoftDeleteMixin, Base):
    """询盘表模型"""
    __tablename__ = "inquiries"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(_uuid_lib.uuid4()))
    name = Column(String(100), nullable=False)
    # phone 可空：公开询盘允许"只留邮箱"（routes/inquiries.py 的
    # require_contact_channel 一直允许 phone 或 email 二选一，列约束此前与
    # 校验口径不一致，导致 email-only 询盘落库必 500）。见迁移 113。
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    product = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    is_active = Column(Boolean, nullable=False, default=True)
    source_channel = Column(String(50), nullable=True)
    session_id = Column(String(64), nullable=True, index=True)
    landing_path = Column(String(500), nullable=True)
    last_click_label = Column(String(300), nullable=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    assigned_to = Column(String(36), nullable=True, index=True)
    source_utm = Column(Text, nullable=True)
    publish_task_id = Column(String(36), nullable=True, index=True)
    meddpicc_json = Column(Text, nullable=True)
    # ── 全链路归因字段 ──
    source_url = Column(String(1000), nullable=True, comment="来源页面完整 URL")
    source_keyword = Column(String(300), nullable=True, comment="搜索关键词")
    ai_search_engine = Column(String(50), nullable=True, comment="AI 搜索引擎来源: deepseek/chatgpt/gemini/perplexity/baidu_ai")
    attribution_channel = Column(String(50), nullable=True, comment="归因渠道: seo/customer_finder/email/social/ai_search/referral/direct")
    attribution_data = Column(Text, nullable=True, comment="归因详情 JSON: {page_id, article_id, geo_score, ...}")
    customer_finder_id = Column(String(36), nullable=True, index=True, comment="关联的 Customer Finder 结果 ID")
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    wechat = Column(String(100), nullable=True)
    quotes = relationship("Quote", back_populates="inquiry")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<Inquiry(name={self.name}, status={self.status})>"
