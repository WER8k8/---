import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
from app.core.database import Base, UUID_TYPE

class JSONType(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}

class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    parent_id = Column(UUID_TYPE, ForeignKey("categories.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    children = relationship("Category", back_populates="parent", remote_side=[id], lazy="select")
    parent = relationship("Category", remote_side=[id], lazy="select")
    products = relationship("Product", back_populates="category", lazy="select")

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(UUID_TYPE, ForeignKey("categories.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    subtitle = Column(String(300))
    description = Column(Text)
    technical_params = Column(Text)
    application_scenarios = Column(Text)
    advantages = Column(Text)
    specifications = Column(JSONType, default={})
    specifications_text = Column(String(200))
    density = Column(String(50))
    strength = Column(String(50))
    thermal_conductivity = Column(String(50))
    unit_weight = Column(String(50))
    fire_rating = Column(String(20))
    image_url = Column(String(500))
    meta_title = Column(String(200))
    meta_description = Column(String(500))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    category = relationship("Category", back_populates="products", lazy="select")


class ProductDocument(Base):
    __tablename__ = "product_documents"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(UUID_TYPE, ForeignKey("products.id"), nullable=False, index=True)
    doc_type = Column(String(20), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    description = Column(String(500))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    product = relationship("Product", backref="documents")
