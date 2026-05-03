import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base, UUID_TYPE


class ContentPage(Base):
    __tablename__ = "content_pages"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    content = Column(Text)
    summary = Column(String(500))
    page_type = Column(String(50), default="page", index=True)
    status = Column(String(20), default="draft", nullable=False, index=True)
    author_id = Column(UUID_TYPE, nullable=True, index=True)
    view_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_pages_type_status_active', 'page_type', 'status', 'is_active'),
        Index('idx_pages_created_desc', 'created_at', postgresql_ops={'created_at': 'DESC'}),
    )
    
    versions = relationship("ContentVersion", back_populates="page", cascade="all, delete-orphan")


class ContentVersion(Base):
    __tablename__ = "content_versions"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(UUID_TYPE, ForeignKey("content_pages.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    summary = Column(String(500))
    change_log = Column(String(500))
    author_id = Column(UUID_TYPE, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    page = relationship("ContentPage", back_populates="versions")

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
