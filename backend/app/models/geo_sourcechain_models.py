"""GEO SourceChain Models - SourceChain GEO Engine database models (non-alert tables)

This module defines the database tables required by the SourceChain GEO engine,
excluding alert tables (which are in geo_alert_db_models.py).
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, Date, JSON
from sqlalchemy.orm import relationship

from app.core.database import UUID_TYPE, Base


class MaterialSpec(Base):
    """Material specifications table (产品规格表)"""
    __tablename__ = "material_specs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_slug = Column(String(255), unique=True, nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    category = Column(String(100))
    density_kg_m3 = Column(Integer)
    strength_mpa = Column(Numeric(6, 2))
    thermal_conductivity = Column(Numeric(6, 3))
    factory_price = Column(Numeric(10, 2))
    price_currency = Column(String(10), default='CNY')
    price_valid_until = Column(Date)
    phone = Column(String(50))
    status = Column(String(30), default='active')
    created_at = Column(DateTime(timezone=True), server_default='NOW()')
    updated_at = Column(DateTime(timezone=True), server_default='NOW()', onupdate='NOW()')
    # Relationships
    content_chunks = relationship("ContentChunk", back_populates="material_spec")
    lead_inquiries = relationship("LeadInquiry", back_populates="material_spec")


class ContentChunk(Base):
    """Content chunks table (内容块表)"""
    __tablename__ = "content_chunks"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(UUID_TYPE, ForeignKey("material_specs.id", ondelete="CASCADE"))
    keyword = Column(String(255), nullable=False, index=True)
    intent = Column(Text, nullable=False)
    chunk_type = Column(String(50), nullable=False)
    title = Column(String(255))
    content = Column(Text, nullable=False)
    jsonld = Column(JSON, default=dict)
    # Note: embedding field requires pgvector extension
    # embedding = Column(Vector(768))  # Uncomment when pgvector is available
    rag_score = Column(Numeric(5, 4))
    quality_status = Column(String(30), default='draft')
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default='NOW()')
    updated_at = Column(DateTime(timezone=True), server_default='NOW()', onupdate='NOW()')
    # Relationships
    material_spec = relationship("MaterialSpec", back_populates="content_chunks")


class SERPSnapshot(Base):
    """SERP snapshots table (搜索引擎结果页快照表)"""
    __tablename__ = "serp_snapshots"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    keyword = Column(String(255), nullable=False, index=True)
    platform = Column(String(100), nullable=False)
    rank_position = Column(Integer)
    title = Column(Text)
    url = Column(Text)
    snippet = Column(Text)
    extracted_features = Column(JSON, default=dict)
    crawl_status = Column(String(30), default='success')
    error_message = Column(Text)
    crawled_at = Column(DateTime(timezone=True), server_default='NOW()')


class LeadInquiry(Base):
    """Lead inquiries table (询盘信息表)"""
    __tablename__ = "lead_inquiries"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(UUID_TYPE, ForeignKey("material_specs.id", ondelete="SET NULL"), nullable=True)
    keyword = Column(String(255))
    name = Column(String(100))
    phone = Column(String(50))
    region = Column(String(255))
    distance_km = Column(Numeric(10, 2))
    quantity_m3 = Column(Numeric(12, 2))
    estimated_price = Column(Numeric(12, 2))
    message = Column(Text)
    source_url = Column(Text)
    source_channel = Column(String(100))
    ip_hash = Column(String(128))
    status = Column(String(30), default='new')
    created_at = Column(DateTime(timezone=True), server_default='NOW()', index=True)
    # Relationships
    material_spec = relationship("MaterialSpec", back_populates="lead_inquiries")


class ReleaseGuard(Base):
    """Release guards table (发布守护记录表)"""
    __tablename__ = "release_guards"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    version = Column(String(100), nullable=False)
    guard_type = Column(String(80), nullable=False)
    status = Column(String(30), nullable=False)
    metrics = Column(JSON, nullable=False, default='{}')
    rollback_version = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default='NOW()')


# Indexes
Index("idx_material_specs_slug", MaterialSpec.product_slug)
Index("idx_content_chunks_keyword", ContentChunk.keyword)
# Index("idx_content_chunks_embedding", ContentChunk.embedding, postgresql_using="ivfflat")  # Requires pgvector
Index("idx_serp_snapshots_keyword", SERPSnapshot.keyword)
Index("idx_lead_inquiries_created_at", LeadInquiry.created_at)
