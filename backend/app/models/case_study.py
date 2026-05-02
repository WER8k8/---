import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base, UUID_TYPE

class CaseStudy(Base):
    __tablename__ = "case_studies"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(UUID_TYPE, ForeignKey("products.id"), nullable=True, index=True)
    project_name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    client_name = Column(String(255))
    materials_used = Column(String(500))
    construction_area = Column(String(100))
    project_date = Column(String(50))
    location = Column(String(255))
    project_address = Column(String(255))
    description = Column(Text)
    cover_image = Column(String(500))
    status = Column(String(20), default="draft")
    sort_order = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    images = relationship("CaseImage", backref="case_study", cascade="all, delete-orphan", order_by="CaseImage.sort_order")
    product = relationship("Product", backref="case_studies")


class CaseImage(Base):
    __tablename__ = "case_images"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(UUID_TYPE, ForeignKey("case_studies.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    image_alt = Column(String(255))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
