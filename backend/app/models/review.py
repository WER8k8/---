# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""评价反馈模型"""

import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import UUID_TYPE, Base


class Review(Base):
    """评价表模型"""
    __tablename__ = "reviews"
    id = Column(UUID_TYPE, primary_key=True, index=True)
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(UUID_TYPE, ForeignKey("products.id"), nullable=False, index=True)
    rating = Column(Float, nullable=False, index=True)  # 评分 1-5
    content = Column(Text, nullable=True)  # 评价内容
    images = Column(Text, nullable=True)  # 评价图片，JSON数组格式
    status = Column(String(20), default="pending", nullable=False, index=True)  # 状态：pending, approved, rejected
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    # 关联关系
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<Review(id={self.id}, user_id={self.user_id}, product_id={self.product_id}, rating={self.rating})>"
    
    @property
    def images_list(self):
        """获取评价图片列表"""
        if not self.images:
            return []
        try:
            return json.loads(self.images)
        except json.JSONDecodeError:
            return []
    
    @images_list.setter
    def images_list(self, value):
        """设置评价图片列表"""
        if value is None:
            self.images = None
        else:
            self.images = json.dumps(value)
