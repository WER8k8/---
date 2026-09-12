"""
Chat Session Model - AI对话会话模型
AI聊天会话（一个会话包含多条消息）
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base, UUID_TYPE


class ChatSession(Base):
    """AI对话会话表模型"""
    __tablename__ = "chat_sessions"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    session_name = Column(String(255), nullable=True)  # 会话名称（用户自定义）
    model_used = Column(String(100), nullable=True)  # 使用的模型
    total_tokens = Column(Integer, default=0)
    status = Column(String(50), default="active", index=True)  # active/archived
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    # 关系
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<ChatSession(name={self.session_name}, status={self.status})>"
