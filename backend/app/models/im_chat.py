"""聊天消息数据库模型（IM用户间聊天，与AI聊天分开）"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base, UUID_TYPE


class IMMessage(Base):
    """IM聊天消息模型（用户间实时聊天）"""
    __tablename__ = "im_messages"
    id = Column(String(36), primary_key=True, index=True)
    sender_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    # text, image, file, system
    message_type = Column(String(20), default="text")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow)

    # 关联关系
    sender = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_messages")
    receiver = relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_messages")


class IMSession(Base):
    """IM聊天会话模型（用户间聊天会话）"""
    __tablename__ = "im_sessions"
    id = Column(String(36), primary_key=True, index=True)
    user1_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False)
    user2_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False)
    last_message_id = Column(String(36), ForeignKey("im_messages.id"))
    unread_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow)

    # 关联关系
    last_message = relationship("IMMessage")


class UserStatus(Base):
    """用户在线状态模型"""
    __tablename__ = "user_status"
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), primary_key=True)
    # online, offline, busy, away
    status = Column(String(20), default="offline")
    last_active_at = Column(DateTime, default=datetime.utcnow)
    device_type = Column(String(20))  # web, mobile, desktop
    # 关联关系
    user = relationship("User", back_populates="status")
