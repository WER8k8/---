"""通知模型"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import UUID_TYPE, Base


class Notification(Base):
    """通知表模型"""
    __tablename__ = "notifications"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, index=True)  # info, warning, error, success
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    # 关系
    user = relationship("User", back_populates="notifications")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<Notification(id={self.id}, title={self.title}, type={self.type})>"
