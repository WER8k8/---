# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Merchant Profile Model - 商家资料模型
用于存储商家的公司信息、认证状态、联系方式等
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base, UUID_TYPE


class MerchantProfile(Base):
    """商家资料表模型"""
    __tablename__ = "merchant_profiles"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    company_name = Column(String(255), nullable=False)
    company_address = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    business_license = Column(String(255), nullable=True)  # 营业执照
    verified = Column(Boolean, default=False, index=True)  # 是否认证
    verification_documents = Column(Text, nullable=True)  # JSON字符串，存储认证文档URLs
    contact_person = Column(String(100), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    whatsapp_number = Column(String(50), nullable=True)
    wechat_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    # 关系
    user = relationship("User", back_populates="merchant_profile")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<MerchantProfile(company={self.company_name}, verified={self.verified})>"
