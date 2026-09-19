# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
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


def _enum_values(enum_cls):
    """SQLAlchemy 以枚举 value（小写）落库，与 API/VALID_* 白名单一致。"""
    return [e.value for e in enum_cls]


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
        Enum(
            OrderStatus,
            name="order_status_enum",
            values_callable=_enum_values,
            validate_strings=True,
        ),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
    )  # ORCH-08/09: 统一状态枚举（库内存 value 小写）
    payment_status = Column(
        Enum(
            PaymentStatus,
            name="payment_status_enum",
            values_callable=_enum_values,
            validate_strings=True,
        ),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
    )  # ORCH-09: 统一支付状态枚举（库内存 value 小写）
    shipping_address = Column(Text, nullable=True)
    shipping_method = Column(String(100), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    access_token = Column(String(64), nullable=True, index=True)  # 买家订单访问令牌（order-token 鉴权）
    estimated_delivery = Column(DateTime(timezone=True), nullable=True)
    # ── 外贸 7 步履约补字段（P/I 定金核销 + 发运单证 CI/箱单套打数据）──
    incoterms = Column(String(10), nullable=True)              # 贸易术语：FOB/CIF/DDP…
    payment_terms = Column(String(50), nullable=True)          # 付款方式：T/T 30%定金+70%发货前
    deposit_ratio = Column(Numeric(5, 2), nullable=True)       # 定金比例(%)
    deposit_amount = Column(Numeric(10, 2), nullable=True)     # 定金金额
    port_of_loading = Column(String(100), nullable=True)       # 起运港
    port_of_discharge = Column(String(100), nullable=True)     # 目的港
    gross_weight = Column(Numeric(12, 3), nullable=True)       # 毛重(kg)
    net_weight = Column(Numeric(12, 3), nullable=True)         # 净重(kg)
    volume = Column(Numeric(12, 3), nullable=True)             # 体积(m³)
    shipping_marks = Column(Text, nullable=True)               # 唛头
    container_no = Column(String(50), nullable=True)           # 集装箱号
    bl_number = Column(String(50), nullable=True)              # 海运提单号
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
