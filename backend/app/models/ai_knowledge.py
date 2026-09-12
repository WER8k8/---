import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base, UUID_TYPE


class AiKnowledgeBase(Base):
    """AI知识库向量表 - 存储商家中文建材资料向量化数据"""
    __tablename__ = "ai_knowledge_base"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)  # 中文知识库原文
    content_type = Column(String(20), default="text", nullable=False)  # text/pdf/url
    file_path = Column(String(500))  # PDF文件路径（如上传PDF）
    embedding_id = Column(String(100))  # pgvector中的向量ID引用
    language = Column(String(10), default="zh", nullable=False)  # 原文语言
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        Index("idx_merchant_kb", "merchant_id", "is_active"),
    )
    merchant = relationship("User", back_populates="knowledge_bases")


class AiChatSession(Base):
    """AI聊天会话表 - 记录买家与AI的对话会话"""
    __tablename__ = "ai_chat_sessions"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    buyer_ip = Column(String(45), index=True)  # IPv4/IPv6
    buyer_country = Column(String(4), index=True)  # 买家国家代码
    buyer_language = Column(String(10))  # 买家使用语言
    buyer_email = Column(String(200))  # 留资邮箱（KPI目标）
    buyer_phone = Column(String(50))  # 留资手机号
    session_status = Column(String(20), default="active", index=True)  # active/closed/converted
    message_count = Column(Integer, default=0)  # 对话轮次
    ai_mode = Column(Boolean, default=True)  # 是否AI托管模式
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        Index("idx_merchant_session", "merchant_id", "session_status"),
    )
    merchant = relationship("User", back_populates="ai_chat_sessions")
    messages = relationship("AiChatMessage", back_populates="session", cascade="all, delete-orphan")


class AiChatMessage(Base):
    """AI聊天消息表 - 存储每轮对话内容"""
    __tablename__ = "ai_chat_messages"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(UUID_TYPE, ForeignKey("ai_chat_sessions.id"), nullable=False, index=True)
    role = Column(String(10), nullable=False, index=True)  # user/assistant/system
    content = Column(Text, nullable=False)
    language = Column(String(10))  # 消息语言
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        Index("idx_session_msg", "session_id", "created_at"),
    )
    session = relationship("AiChatSession", back_populates="messages")
