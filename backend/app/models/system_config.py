# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
System Config Model - 系统配置模型
系统全局配置（汇率、税费、功能开关等）
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
import uuid

from app.core.database import Base, UUID_TYPE


class SystemConfig(Base):
    """系统配置表模型"""
    __tablename__ = "system_config"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(255), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(50), default="string")  # string/number/boolean/json
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)  # 是否允许前端读取
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<SystemConfig(key={self.key}, value={self.value})>"
