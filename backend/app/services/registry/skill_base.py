# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Skill 运行时基类（移植自 Trade AI Agent `app/core/skill_base.py`，MIT，保留出处）。

改造点（合并红线 §融合裁决）：
- 去掉原 `app.config.settings` 依赖，改为本库 `app.core.execution_context`。
- __init__ 注入 tenant_id（原版无租户），满足"全部移植件强制 tenant_id"红线。
- datetime 统一 timezone-aware。
- 生命周期钩子 on_start/on_success/on_failure/on_skip 与轮18 skills 表
  validators.lifecycle（083.1）字段契约一一对应。

用途：作为 skills 表的运行时执行层——表管版本/权限/租户开关，本类管执行。
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from app.core.execution_context import ExecutionContext


class SkillStatus(Enum):
    """Skill 执行状态。"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class BaseSkill(ABC):
    """所有 Skill 插件必须继承并实现 execute。"""

    # 元信息（子类必须设置）
    name: str
    display_name: str
    description: str
    category: str
    version: str = "1.0.0"

    config_schema: dict[str, Any] = {}
    default_config: dict[str, Any] = {}

    input_schema: dict[str, Any] = {}
    output_schema: dict[str, Any] = {}

    # 执行设置（对齐 083.1 skills 运行字段）
    timeout: int = 300
    retry_count: int = 3
    retry_delay: int = 1

    _status = SkillStatus.PENDING
    _start_time: Optional[datetime] = None
    _end_time: Optional[datetime] = None
    _error: Optional[Exception] = None

    def __init__(self, config: Optional[dict[str, Any]] = None, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.config = {**self.default_config, **(config or {})}
        self._validate_config()

    def _validate_config(self) -> None:
        """可被子类覆盖的自定义校验。"""

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> dict[str, Any]:
        """核心执行方法，子类必须实现。"""

    def validate_input(self, data: dict[str, Any]) -> bool:
        schema = self.input_schema or {}
        properties = schema.get("properties") if isinstance(schema, dict) else None
        if isinstance(properties, dict):
            for field, field_schema in properties.items():
                if isinstance(field_schema, dict) and field_schema.get("required", False) and field not in data:
                    return False
            return True
        for field, field_schema in schema.items():
            if isinstance(field_schema, dict) and field_schema.get("required", False) and field not in data:
                return False
        return True

    def validate_output(self, data: dict[str, Any]) -> bool:
        schema = self.output_schema or {}
        properties = schema.get("properties") if isinstance(schema, dict) else None
        if isinstance(properties, dict):
            for field, field_schema in properties.items():
                if isinstance(field_schema, dict) and field_schema.get("required", False) and field not in data:
                    return False
            return True
        for field, field_schema in schema.items():
            if isinstance(field_schema, dict) and field_schema.get("required", False) and field not in data:
                return False
        return True

    def on_start(self, context: ExecutionContext) -> None:
        self._status = SkillStatus.RUNNING
        self._start_time = _now()
        context.add_step(f"{self.name}_start")

    def on_success(self, context: ExecutionContext, output: dict[str, Any]) -> None:
        self._status = SkillStatus.SUCCESS
        self._end_time = _now()
        context.add_step(f"{self.name}_success")

    def on_failure(self, error: Exception, context: ExecutionContext) -> None:
        self._status = SkillStatus.FAILED
        self._error = error
        self._end_time = _now()
        context.add_step(f"{self.name}_failed")
        context.set_error(
            f"Skill {self.name} failed: An internal error occurred",
            None,
        )

    def on_skip(self, context: ExecutionContext, reason: str) -> None:
        self._status = SkillStatus.SKIPPED
        self._end_time = _now()
        context.add_step(f"{self.name}_skipped")
        context.set_state(f"{self.name}_skip_reason", reason)

    def get_execution_time(self) -> float:
        if self._start_time and self._end_time:
            return (self._end_time - self._start_time).total_seconds()
        return 0.0

    def get_status(self) -> SkillStatus:
        return self._status

    def get_error(self) -> Optional[Exception]:
        return self._error

    def get_metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "config_schema": self.config_schema,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
        }

    def get_info(self) -> dict[str, Any]:
        return {
            **self.get_metadata(),
            "status": self._status.value if self._status else None,
            "execution_time": self.get_execution_time(),
            "error": str(self._error) if self._error else None,
        }

    async def run(self, context: ExecutionContext) -> dict[str, Any]:
        if not self.validate_input(context.input_data):
            raise ValueError(f"Invalid input for skill {self.name}")
        self.on_start(context)
        last_error: Optional[Exception] = None
        for attempt in range(self.retry_count + 1):
            try:
                output = await self.execute(context)
                if not self.validate_output(output):
                    raise ValueError(f"Invalid output from skill {self.name}")
                self.on_success(context, output)
                return output
            except Exception as e:  # noqa: BLE001
                last_error = e
                if attempt < self.retry_count:
                    import asyncio

                    await asyncio.sleep(self.retry_delay * (2**attempt))
                else:
                    self.on_failure(e, context)
                    raise
        raise last_error or Exception("Skill execution failed")

    @classmethod
    def get_all_subclasses(cls) -> list["BaseSkill"]:
        return cls.__subclasses__()


class SkillRegistry:
    """Skill 插件类注册表。"""

    _skills: dict[str, type] = {}

    @classmethod
    def register(cls, skill_class: type) -> type:
        if not issubclass(skill_class, BaseSkill):
            raise TypeError(f"{skill_class} must be a subclass of BaseSkill")
        cls._skills[skill_class.name] = skill_class
        return skill_class

    @classmethod
    def get(cls, name: str) -> Optional[type]:
        return cls._skills.get(name)

    @classmethod
    def list_all(cls) -> dict[str, type]:
        return cls._skills.copy()

    @classmethod
    def create_instance(
        cls,
        name: str,
        config: Optional[dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> Optional[BaseSkill]:
        skill_class = cls.get(name)
        if skill_class:
            return skill_class(config, tenant_id=tenant_id)
        return None

    @classmethod
    def get_categories(cls) -> list[str]:
        return sorted({c.category for c in cls._skills.values()})

    @classmethod
    def get_by_category(cls, category: str) -> dict[str, type]:
        return {
            name: skill_class
            for name, skill_class in cls._skills.items()
            if skill_class.category == category
        }


def register_skill(cls):
    """注册 Skill 插件类的装饰器。"""
    return SkillRegistry.register(cls)