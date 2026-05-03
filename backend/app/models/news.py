from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, func
from app.core.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    subtitle = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    cover_image = Column(String(500), nullable=True)
    category = Column(String(50), nullable=False, index=True)  # company, industry, product, technology
    tags = Column(String(500), nullable=True)  # JSON array of tags
    author = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True)
    view_count = Column(Integer, default=0)
    is_published = Column(Boolean, default=False, index=True)
    published_at = Column(DateTime, nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NewsCategory(Base):
    __tablename__ = "news_categories"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
