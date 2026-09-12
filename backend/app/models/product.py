"""产品和分类模型 — 支持 JSON 规格参数、文档管理。"""
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.core.database import UUID_TYPE, Base
from app.models.soft_delete import SoftDeleteMixin


class JSONType(TypeDecorator):
    impl = Text
    def process_bind_param(self, value, dialect):
        """process_bind_param。

        参数说明：
        :param self: 参数 self
        :param value: 参数 value
        :param dialect: 参数 dialect
        :return: 返回处理结果。
        """
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        """process_result_value。

        参数说明：
        :param self: 参数 self
        :param value: 参数 value
        :param dialect: 参数 dialect
        :return: 返回处理结果。
        """
        if value is None:
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[str] = mapped_column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[str | None] = mapped_column(UUID_TYPE, ForeignKey("categories.id"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc))

    children = relationship("Category", back_populates="parent", foreign_keys="Category.parent_id", lazy="select")
    parent = relationship("Category", back_populates="children", remote_side=[id], foreign_keys="Category.parent_id", lazy="select")
    products = relationship("Product", back_populates="category", lazy="select")


class Product(SoftDeleteMixin, Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    # ADR-001 租户归一：nullable 待写入方补真值；非空约束在回填迁移中收紧
    tenant_id: Mapped[str | None] = mapped_column(UUID_TYPE, nullable=True, index=True)
    category_id: Mapped[str] = mapped_column(UUID_TYPE, ForeignKey("categories.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    subtitle: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    technical_params: Mapped[str | None] = mapped_column(Text)
    application_scenarios: Mapped[str | None] = mapped_column(Text)
    advantages: Mapped[str | None] = mapped_column(Text)
    specifications: Mapped[dict | None] = mapped_column(JSONType, default={})
    specifications_text: Mapped[str | None] = mapped_column(String(200))
    density: Mapped[str | None] = mapped_column(String(50))
    strength: Mapped[str | None] = mapped_column(String(50))
    thermal_conductivity: Mapped[str | None] = mapped_column(String(50))
    unit_weight: Mapped[str | None] = mapped_column(String(50))
    fire_rating: Mapped[str | None] = mapped_column(String(20))
    image_url: Mapped[str | None] = mapped_column(String(500))
    meta_title: Mapped[str | None] = mapped_column(String(200))
    meta_description: Mapped[str | None] = mapped_column(String(500))
    # ── 英文字段（外贸 GEO 双语） ──
    name_en: Mapped[str | None] = mapped_column(String(200), comment="English product name")
    subtitle_en: Mapped[str | None] = mapped_column(String(300), comment="English subtitle")
    description_en: Mapped[str | None] = mapped_column(Text, comment="English description")
    technical_params_en: Mapped[str | None] = mapped_column(Text, comment="English technical parameters")
    advantages_en: Mapped[str | None] = mapped_column(Text, comment="English advantages")
    application_scenarios_en: Mapped[str | None] = mapped_column(Text, comment="English application scenarios")
    meta_title_en: Mapped[str | None] = mapped_column(String(200), comment="English SEO title")
    meta_description_en: Mapped[str | None] = mapped_column(String(500), comment="English SEO description")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc))

    category = relationship("Category", back_populates="products", lazy="select")
    reviews = relationship("Review", back_populates="product", lazy="select")
    order_items = relationship("OrderItem", back_populates="product", lazy="select")
    images = relationship("ProductImage", back_populates="product", lazy="select")
    ai_recommendations = relationship("AIRecommendation", back_populates="product", lazy="select")
    faqs = relationship("ProductFaq", back_populates="product", lazy="select", order_by="ProductFaq.sort_order")
    documents = relationship("ProductDocument", back_populates="product", lazy="select")


class ProductDocument(Base):
    __tablename__ = "product_documents"
    id: Mapped[str] = mapped_column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(UUID_TYPE, ForeignKey("products.id"), nullable=False, index=True)
    doc_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    product = relationship("Product", back_populates="documents")


class ProductFaq(Base):
    """产品 FAQ — 中英双语，GEO 优化核心组件"""
    __tablename__ = "product_faqs"
    id: Mapped[str] = mapped_column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(UUID_TYPE, ForeignKey("products.id"), nullable=False, index=True)
    question_zh: Mapped[str] = mapped_column(String(500), nullable=False, comment="中文问题")
    answer_zh: Mapped[str] = mapped_column(Text, nullable=False, comment="中文回答")
    question_en: Mapped[str | None] = mapped_column(String(500), comment="English question")
    answer_en: Mapped[str | None] = mapped_column(Text, comment="English answer")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc))
    product = relationship("Product", back_populates="faqs")


# 兼容导出：ProductImage 物理定义在 app.models.product_image，在此重导出以满足各模块调用契约
try:
    from app.models.product_image import ProductImage  # noqa: F401
except ImportError:
    pass
