import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Boolean
from app.core.database import Base, UUID_TYPE


class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    phone = Column(String(50), nullable=False, index=True)
    email = Column(String(200), index=True)
    product = Column(String(100), index=True)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
