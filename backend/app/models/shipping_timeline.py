# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base, UUID_TYPE


class ShippingTimeline(Base):
    """物流进度时间线配置表 - IP动态匹配清关证书"""
    __tablename__ = "shipping_timeline"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    country_code = Column(String(4), nullable=False, index=True)  # NG/SA/DE/KE/RU
    step_1_title = Column(String(100), nullable=False)  # "Custom Production"
    step_1_desc = Column(Text)  # "确认规格，工厂拉丝编织、涂覆胶水"
    step_1_days = Column(String(20))  # "3-5 Days"
    step_2_title = Column(String(100), nullable=False)  # "Compliance & Packing"
    step_2_desc = Column(Text)  # "本地质检，申请当地清关所需证书"
    step_2_days = Column(String(20))  # "2 Days"
    step_2_badge = Column(String(100))  # "Support SONCAP / PVOC / SABER"
    step_3_title = Column(String(100), nullable=False)  # "Ocean Shipping"
    step_3_desc = Column(Text)  # "订舱装箱，直达到港"
    step_3_days = Column(String(20))  # "Guaranteed Space"
    step_4_title = Column(String(100), nullable=False)  # "Destination Assistance"
    step_4_desc = Column(Text)  # "到岸后提供货代资源，协助清关"
    step_4_days = Column(String(20))  # "-"
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        Index("idx_merchant_shipping", "merchant_id", "country_code"),
    )
    merchant = relationship("User", backref="shipping_timelines")


class AnalyticsEvent(Base):
    """点击漏斗监测事件表 - 记录用户行为转化漏斗"""
    __tablename__ = "analytics_events"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # page_load/im_click/form_open/form_submit
    product_id = Column(UUID_TYPE, ForeignKey("products.id"), index=True)
    visitor_ip = Column(String(45), index=True)
    visitor_country = Column(String(4), index=True)
    visitor_language = Column(String(10))
    session_id = Column(String(100), index=True)  # 会话ID（用于去重和漏斗分析）
    referrer = Column(String(500))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    __table_args__ = (
        Index("idx_merchant_event", "merchant_id", "event_type", "created_at"),
    )
    merchant = relationship("User", backref="analytics_events")
    product = relationship("Product", backref="analytics_events")


class InquiryExtended(Base):
    """询盘扩展表 - 在原inquiry表基础上增加建材垂直字段"""
    __tablename__ = "inquiry_extended"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    inquiry_id = Column(UUID_TYPE, ForeignKey("inquiries.id"), nullable=False, index=True, unique=True)
    product_spec = Column(Text)  # 买家提交的规格要求（OCR/语音识别结果）
    quantity = Column(String(50))  # 需求量
    target_port = Column(String(100))  # 目的港（拉各斯/蒙巴萨等）
    urgency = Column(String(20))  # 紧急程度：normal/urgent
    source_channel = Column(String(20))  # 来源渠道：whatsapp/telegram/form/livechat
    ai_session_id = Column(UUID_TYPE, ForeignKey("ai_chat_sessions.id"))  # 关联AI会话
    is_converted = Column(Boolean, default=False)  # 是否转化（已下单）
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    inquiry = relationship("Inquiry", backref="extended", uselist=False)
    ai_session = relationship("AiChatSession", backref="inquiry")
