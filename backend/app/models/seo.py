import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Boolean
from app.core.database import Base, UUID_TYPE


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    keyword = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), nullable=False, index=True)
    search_volume = Column(Integer, default=0)
    difficulty = Column(String(20), default="medium")
    current_ranking = Column(Integer, nullable=True)
    target_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class KeywordRanking(Base):
    __tablename__ = "keyword_rankings"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    keyword_id = Column(UUID_TYPE, nullable=False, index=True)
    ranking = Column(Integer)
    page_url = Column(String(500))
    search_engine = Column(String(50), default="baidu")
    checked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class SiteAudit(Base):
    __tablename__ = "site_audits"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String(500))
    status = Column(String(20), default="pending", nullable=False)
    audit_type = Column(String(50), nullable=False)
    score = Column(Float)
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    warning_issues = Column(Integer, default=0)
    report_data = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AiOptimizationLog(Base):
    __tablename__ = "ai_optimization_logs"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=False)
    optimization_type = Column(String(50), nullable=False)
    original_content = Column(Text)
    optimized_content = Column(Text)
    model_used = Column(String(100))
    tokens_used = Column(Integer, default=0)
    score_before = Column(Float)
    score_after = Column(Float)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class LlmsConfig(Base):
    __tablename__ = "llms_config"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    section = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
