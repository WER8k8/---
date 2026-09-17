# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Base Executor Contract for Hermes Orchestration.

三份契约之一（见 docs/架构设计-智能编排内核-任务图驱动-2026-09-06.md §2 契约三）。

⚠️ 此前本文件只有 `get_executor_name()` + `run()`，**能力声明契约缺失** ——
   导致拆解器只能靠硬编码的 KNOWN_CAPABILITIES 与模板来"猜"有哪些能力，
   加一个执行器必须改 planner 代码，违背"万能皆可插"。

现在补齐 `get_capabilities()`：执行器自述它能做什么，注册表可聚合，
拆解器据此产出合法图 —— **加执行器 = 加文件 + 声明能力，planner 零改动**。
"""
import abc
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode


class ExecutorContext:
    def __init__(self, db: Session, tenant_id: str, plan_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.plan_id = plan_id


class BaseExecutor(abc.ABC):
    """Abstract base class for all Hermes executors."""

    @classmethod
    @abc.abstractmethod
    def get_executor_name(cls) -> str:
        """Return the unique name of this executor (e.g., 'accio', 'deerflow')."""
        pass

    @abc.abstractmethod
    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        """Execute the task node and return the result."""
        pass

    # ── 契约三：能力声明（新）────────────────────────────────
    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        """自述本执行器支持的能力。默认空 = 未声明（不报错，向后兼容）。

        返回结构（字段全部可选，缺省即"未声明"）：
            {
              "site.generate": {
                  "desc": "一句话说明",
                  "input": ["product_name", "product_images"],   # 期望入参
                  "output": ["url", "site_id"],                  # 产出字段
                  "cost": {"tokens": 50000, "seconds": 600},     # 粗估开销
                  "needs_approval": False,                       # 是否默认需人审
              },
              ...
            }

        用途：① 拆解器据此校验 capability 是否真实存在；
              ② 生成图谱时给出输入/输出提示；
              ③ 预算与审批的默认值来源。
        """
        return {}

    @classmethod
    def capability_names(cls) -> list[str]:
        """便捷方法：只取能力名列表。"""
        return sorted(cls.get_capabilities().keys())


class ExecutorRegistry:
    _executors: Dict[str, BaseExecutor] = {}

    @classmethod
    def register(cls, executor: BaseExecutor):
        cls._executors[executor.get_executor_name()] = executor

    @classmethod
    def get(cls, name: str) -> BaseExecutor:
        if name not in cls._executors:
            raise ValueError(f"Executor '{name}' not found in registry. Registered: {list(cls._executors.keys())}")
        return cls._executors[name]

    @classmethod
    def has(cls, name: str) -> bool:
        return name in cls._executors

    @classmethod
    def list_executors(cls) -> list[str]:
        return list(cls._executors.keys())

    # ── 能力聚合（新）──────────────────────────────────────
    @classmethod
    def all_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        """聚合所有已注册执行器的能力 → {capability: {executor, ...spec}}。

        重名能力：**先注册者优先**，并在 spec 里记录冲突（不静默覆盖）。
        """
        out: Dict[str, Dict[str, Any]] = {}
        conflicts: list[str] = []
        for name, ex in cls._executors.items():
            try:
                caps = ex.get_capabilities() or {}
            except Exception:  # noqa: BLE001 — 单个执行器声明异常不影响整体
                continue
            for cap, spec in caps.items():
                if cap in out:
                    conflicts.append(f"{cap}:{out[cap].get('executor')}vs{name}")
                    continue
                merged = dict(spec or {})
                merged["executor"] = name
                out[cap] = merged
        if conflicts:
            import logging
            logging.getLogger(__name__).warning(
                "ExecutorRegistry: 能力重名冲突（先注册者优先）: %s", conflicts
            )
        return out

    @classmethod
    def capability_names(cls) -> list[str]:
        return sorted(cls.all_capabilities().keys())
