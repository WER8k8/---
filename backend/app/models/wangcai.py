# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Wangcai Session / QA Log Models - 旺财访客会话与问答日志（总纲 §7A.3 / 迁移 094）

红线：
- 禁止复用 chat_sessions（user_id NOT NULL，公开访客无账号，实测 models/chat_session.py L18）；
- wangcai_sessions 用匿名 visitor_ref，(tenant_id, visitor_ref) 唯一——访客串站=数据事故（指南 3.6）；
- wangcai_qa_log 一表两用：N3 多轮上下文 + N7 证据（citation_refs/lead_converted），
  model/tokens 列为 N8 计量供数（指南 4.4-4）。
- 隐私：访客会话属个人数据，90 天过期清理走现有 gdpr 策略（指南 3.1）。
"""
import uuid

from sqlalchemy import (Boolean, CheckConstraint, Column, DateTime,
                        ForeignKey, Integer, String, Text)
from sqlalchemy.sql import func

from app.core.database import Base, UUID_TYPE


class WangcaiSession(Base):
    """旺财访客会话（匿名 visitor_ref；与租户绑定）"""
    __tablename__ = "wangcai_sessions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False)
    visitor_ref = Column(String(128), nullable=False)
    language = Column(String(10), nullable=True)
    intent_history = Column(Text, nullable=True)    # JSON 数组
    summary = Column(Text, nullable=True)           # 超窗摘要（指南 3.2）
    turn_count = Column(Integer, nullable=False, default=0)
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<WangcaiSession(tenant={self.tenant_id}, visitor={self.visitor_ref})>"


class WangcaiQaLog(Base):
    """旺财问答日志：N3 上下文 + N7 证据一表两用（model/tokens 为 N8 计量证据）"""
    __tablename__ = "wangcai_qa_log"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_wangcai_qa_log_role"),
    )
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("wangcai_sessions.id"), nullable=True)
    role = Column(String(12), nullable=False)       # user | assistant
    intent = Column(String(40), nullable=True)
    content = Column(Text, nullable=True)
    citation_refs = Column(Text, nullable=True)     # JSON 数组（来源引用，Evidence）
    model = Column(String(60), nullable=True)       # N4/N8 计量
    tokens = Column(Integer, nullable=True)
    lead_converted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<WangcaiQaLog(session={self.session_id}, role={self.role})>"
