"""
Product Image Model - 产品图片模型
产品的多张图片（支持主图、排序）
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base, UUID_TYPE


class ProductImage(Base):
    """产品图片表模型"""
    __tablename__ = "product_images"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(UUID_TYPE, ForeignKey("products.id"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    alt_text = Column(String(255), nullable=True)  # 图片alt（SEO）
    sort_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)  # 是否主图
    created_at = Column(DateTime(timezone=True), default=func.now())
    # 关系
    product = relationship("Product", back_populates="images")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<ProductImage(product={self.product_id}, primary={self.is_primary})>"
