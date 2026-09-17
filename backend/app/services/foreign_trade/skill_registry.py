# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""外贸 AI 技能注册表 — 动态发现、注册、调用技能。"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from app.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)


@dataclass
class SkillResult:
    """技能执行结果。"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    skill_name: str = ""
    model_used: str = ""
    tokens_used: int = 0


@dataclass
class SkillMeta:
    """技能元数据。"""
    name: str
    display_name: str
    description: str
    category: str  # prospect / outreach / research / competitor / enablement / seo / content
    icon: str
    prompt_template: str
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)


class SkillRegistry:
    """外贸技能注册表 — 所有技能的统一管理器。"""
    _instance: Optional["SkillRegistry"] = None
    _skills: dict[str, SkillMeta] = {}
    def __new__(cls):
        """__new__。

        参数说明：
        :param cls: 参数 cls
        :return: 返回处理结果。
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills = {}
        return cls._instance

    def register(self, meta: SkillMeta):
        """注册一个技能。"""
        self._skills[meta.name] = meta
        logger.info("skill registered: %s (%s)", meta.name, meta.display_name)

    def get(self, name: str) -> Optional[SkillMeta]:
        """get。

        参数说明：
        :param self: 参数 self
        :param name: 参数 name
        :return: 返回处理结果。
        """
        return self._skills.get(name)

    def list_all(self) -> list[dict]:
        """列出所有已注册技能。"""
        return [
            {
                "name": s.name,
                "display_name": s.display_name,
                "description": s.description,
                "category": s.category,
                "icon": s.icon,
            }
            for s in self._skills.values()
        ]

    async def execute(self, name: str, params: dict) -> SkillResult:
        """执行一个技能。"""
        meta = self._skills.get(name)
        if not meta:
            return SkillResult(success=False, error=f"技能 '{name}' 未注册")

        engine = AIEngine()
        llm = engine.llms.get("cost_optimized") or engine.llms.get("deepseek") or engine.llms.get("general")
        if not llm:
            return SkillResult(success=False, error="AI 服务未配置")

        prompt = meta.prompt_template.format(**params)
        try:
            result = llm.invoke(prompt)
            content = result.content.strip()
            # 尝试解析 JSON
            data = content
            if content.startswith("[") or content.startswith("{"):
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    pass
            return SkillResult(
                success=True,
                data=data,
                skill_name=name,
                model_used=getattr(llm, "model_name", "unknown"),
                tokens_used=getattr(result, "usage", {}).get("total_tokens", 0) if hasattr(result, "usage") else 0,
            )
        except Exception as e:
            logger.error("skill %s failed: %s", name, e)
            return SkillResult(success=False, error=str(e), skill_name=name)


# 全局单例
skill_registry = SkillRegistry()
