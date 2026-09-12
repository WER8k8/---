"""Quote Model - 报价模型，商家向买家提供的报价单（B2B RFQ 闭环）。"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, Date, Integer, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base, UUID_TYPE


class Quote(Base):
    """报价表模型"""
    __tablename__ = "quotes"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    # ADR-001 租户归一：tenant_id 为租户维度；merchant_id 保留为交易对手用户外键
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    inquiry_id = Column(UUID_TYPE, ForeignKey("inquiries.id"), nullable=True, index=True)
    merchant_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    rfq_id = Column(UUID_TYPE, ForeignKey("rfqs.id"), nullable=True, index=True)
    opportunity_id = Column(UUID_TYPE, nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD")
    valid_until = Column(Date, nullable=True)
    payment_terms = Column(Text, nullable=True)
    delivery_terms = Column(Text, nullable=True)
    status = Column(String(50), default="draft", index=True)
    pdf_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    inquiry = relationship("Inquiry", back_populates="quotes")
    merchant = relationship("User", back_populates="quotes_as_merchant")
    order = relationship("Order", back_populates="quote")
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<Quote(total={self.total_amount} {self.currency}, status={self.status})>"


class QuoteItem(Base):
    """报价明细行"""
    __tablename__ = "quote_items"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    quote_id = Column(UUID_TYPE, ForeignKey("quotes.id"), nullable=False, index=True)
    product_id = Column(UUID_TYPE, nullable=True, index=True)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=True)
    total_price = Column(Numeric(10, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    quote = relationship("Quote", back_populates="items")