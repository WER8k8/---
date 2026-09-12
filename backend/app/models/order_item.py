"""
Order Item Model - 订单明细模型
订单中的产品明细（一个订单可包含多个产品）
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Integer, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base, UUID_TYPE


class OrderItem(Base):
    """订单明细表模型"""
    __tablename__ = "order_items"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(UUID_TYPE, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(UUID_TYPE, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    specifications = Column(Text, nullable=True)  # JSON字符串，存储选购的规格
    created_at = Column(DateTime(timezone=True), default=func.now())
    # 关系
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<OrderItem(product={self.product_id}, qty={self.quantity})>"
