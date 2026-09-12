import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.core.database import UUID_TYPE, Base


class FeishuBinding(Base):
    __tablename__ = "feishu_bindings"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    feishu_open_id = Column(
        String(200),
        nullable=False,
        unique=True,
        index=True)
    feishu_user_name = Column(String(100), default="")
    bound_user_id = Column(String(36), nullable=False, index=True)
    bound_username = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class FeishuMessageLog(Base):
    __tablename__ = "feishu_message_logs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    feishu_open_id = Column(String(200), nullable=False, index=True)
    message_type = Column(String(20), nullable=False)
    content = Column(Text, default="")
    direction = Column(String(10), nullable=False)
    status = Column(String(20), default="success")
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), nullable=False, index=True)
