# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI 内容生成模板模型"""

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class AITemplate(Base):
    """AI 内容生成模板表"""
    __tablename__ = "ai_templates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, comment="模板名称")
    task_type = Column(String(30), nullable=False, comment="任务类型: optimize/llms_txt/seo_analysis/code/product_gen/polish/general")
    system_prompt = Column(Text, nullable=True, comment="系统提示词")
    user_prompt_template = Column(Text, nullable=False, comment="用户提示词模板，含{{变量}}")
    variables_json = Column(Text, nullable=False, default="[]", comment="可用变量列表JSON数组")
    default_params_json = Column(Text, nullable=False, default='{"temperature":0.7,"max_tokens":2000}', comment="默认生成参数JSON")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序权重")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    def to_dict(self):
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        import json
        return {
            "id": str(self.id),
            "name": self.name,
            "task_type": self.task_type,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "variables_json": self.variables_json or "[]",
            "default_params_json": self.default_params_json or '{"temperature":0.7,"max_tokens":2000}',
            "is_active": self.is_active,
            "sort_order": self.sort_order or 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
