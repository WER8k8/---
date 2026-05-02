import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean
from app.core.database import Base, UUID_TYPE


class ContentPage(Base):
    __tablename__ = "content_pages"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    content = Column(Text)
    summary = Column(String(500))
    page_type = Column(String(50), default="page", index=True)
    status = Column(String(20), default="draft", nullable=False)
    author_id = Column(UUID_TYPE, nullable=True, index=True)
    view_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class SeoMetadata(Base):
    __tablename__ = "seo_metadata"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(50), nullable=False, index=True)
    meta_title = Column(String(200))
    meta_description = Column(String(500))
    meta_keywords = Column(String(300))
    canonical_url = Column(String(500))
    og_title = Column(String(200))
    og_description = Column(String(500))
    og_image = Column(String(500))
    schema_markup = Column(Text)
    noindex = Column(Boolean, default=False)
    h1_tag = Column(String(200))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
