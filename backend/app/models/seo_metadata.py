"""SEO 元数据 — 单表 seo_metadata，resource_* 为主键列，entity_* 为历史别名。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import synonym

from app.core.database import Base, UUID_TYPE


class SeoMetadata(Base):
    __tablename__ = "seo_metadata"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(50), nullable=False, index=True)
    meta_title = Column(String(255))
    meta_description = Column(Text)
    meta_keywords = Column(String(500))
    canonical_url = Column(String(500))
    og_title = Column(String(255))
    og_description = Column(Text)
    og_image = Column(String(500))
    schema_markup = Column(Text)
    noindex = Column(Boolean, default=False, nullable=False)
    h1_tag = Column(String(200))
    hreflang_tags = Column(Text)
    structured_data = Column(Text)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    entity_type = synonym("resource_type")
    entity_id = synonym("resource_id")
    def __repr__(self) -> str:
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<SeoMetadata(resource={self.resource_type}:{self.resource_id})>"


# 历史命名兼容
SEOMetadata = SeoMetadata
