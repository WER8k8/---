import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Boolean, JSON, DateTime
from app.core.database import Base, UUID_TYPE


class SchemaMarkup(Base):
    __tablename__ = "schema_markups"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    schema_type = Column(String(100), nullable=False, index=True)
    content = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    page_url = Column(String(500))
    version = Column(String(20), default="1.0")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class SchemaTemplate(Base):
    __tablename__ = "schema_templates"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    schema_type = Column(String(100), nullable=False, index=True)
    template = Column(JSON, nullable=False)
    description = Column(Text)
    category = Column(String(50), default="general")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))