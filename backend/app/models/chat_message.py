# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Chat Message Model - AI对话消息模型
AI聊天消息（用户消息/助手回复/系统消息）
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base, UUID_TYPE


class ChatMessage(Base):
    """AI对话消息表模型"""
    __tablename__ = "chat_messages"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(UUID_TYPE, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False, index=True)  # user/assistant/system
    content = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=True)
    model = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    # 关系
    session = relationship("ChatSession", back_populates="messages")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<ChatMessage(role={self.role}, content={self.content[:50]})>"
