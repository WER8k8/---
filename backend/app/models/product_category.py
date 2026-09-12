"""
Product Category Model - 产品分类模型
建材产品的分类体系（支持多级分类）
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base, UUID_TYPE


class ProductCategory(Base):
    """产品分类表模型"""
    __tablename__ = "product_categories"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)  # 分类名称（默认语言）
    name_i18n = Column(Text, nullable=True)  # JSON字符串，多语言名称
    slug = Column(String(255), nullable=False, unique=True, index=True)  # URL slug
    parent_id = Column(UUID_TYPE, ForeignKey("product_categories.id"), nullable=True, index=True)
    level = Column(Integer, default=0)  # 层级（0=一级，1=二级...）
    icon_url = Column(String(500), nullable=True)
    sort_order = Column(Integer, default=0)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    # 关系
    parent = relationship("ProductCategory", remote_side=[id], back_populates="children")
    children = relationship("ProductCategory", back_populates="parent")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<ProductCategory(name={self.name}, level={self.level})>"
