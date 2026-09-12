"""
Order Model - 订单模型
B2B交易订单（由报价单转换而来）
"""
from sqlalchemy import Column, Enum, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base, UUID_TYPE
from app.models.enums import OrderStatus, PaymentStatus


class Order(Base):
    """订单表模型"""
    __tablename__ = "orders"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    # ADR-001 租户归一：tenant_id 为租户维度；merchant_id/buyer_id 保留为交易对手用户外键
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    buyer_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    merchant_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    quote_id = Column(UUID_TYPE, ForeignKey("quotes.id"), nullable=True)
    order_number = Column(String(100), nullable=False, unique=True, index=True)  # 订单号
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(
        Enum(OrderStatus, name="order_status_enum"),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
    )  # ORCH-08/09: 统一状态枚举
    payment_status = Column(
        Enum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
    )  # ORCH-09: 统一支付状态枚举
    shipping_address = Column(Text, nullable=True)
    shipping_method = Column(String(100), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    estimated_delivery = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    # 关系
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="orders_as_buyer")
    merchant = relationship("User", foreign_keys=[merchant_id], back_populates="orders_as_merchant")
    quote = relationship("Quote", back_populates="order")
    items = relationship("OrderItem", back_populates="order")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<Order(number={self.order_number}, status={self.status})>"
