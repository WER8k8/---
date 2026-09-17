# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
AI Recommendation Model - AI推荐模型
AI推荐系统的推荐记录（用户-产品推荐对）
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base, UUID_TYPE


class AIRecommendation(Base):
    """AI推荐表模型"""
    __tablename__ = "ai_recommendations"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(UUID_TYPE, ForeignKey("products.id"), nullable=False, index=True)
    score = Column(Numeric(5, 4), nullable=False)  # 推荐分数（0-1）
    reason = Column(Text, nullable=True)  # 推荐理由
    algorithm = Column(String(100), nullable=True)  # 使用的算法
    created_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    # 关系
    user = relationship("User", back_populates="ai_recommendations")
    product = relationship("Product", back_populates="ai_recommendations")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<AIRecommendation(user={self.user_id}, product={self.product_id}, score={self.score})>"
