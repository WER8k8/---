"""Nurture Executor Plugin — 多平台账号养护（养号）。

业务链第 7 环：分发出去的账号需要「养」——按各平台的养护规则推进周期，
避免新号被判定为营销号而限流/封禁。

承载实现（已存在）：
    services/social_nurture_service.create_cycle(...)   —— 建养号周期
    services/social_nurture_service.auto_advance(...)   —— 自动推进
    services/social_nurture_service.get_nurture_profile —— 平台养护规则
    models/nurture_cycle.NurtureCycle                   —— 持久化

能力：
    nurture.create   —— 为某平台账号建养号周期
    nurture.advance  —— 推进已有周期
输入：
    {"platform": "reddit", "account_label": "主号", "platform_account_id": "可选", "rules": {}}
    或 {"cycle_id": "..."} 用于 advance
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"nurture.create", "nurture.advance", "default"})


class NurtureExecutor(BaseExecutor):
    """养号执行器。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "nurture"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"nurture 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})
        cycle_id = str(params.get("cycle_id") or "").strip()

        try:
            from app.services import social_nurture_service as sn

            if cycle_id:
                # 推进既有周期
                result = sn.auto_advance(context.db, cycle_id)
                if result is None:
                    return ExecutorResult(
                        node_id=node.id,
                        status="failed",
                        output={"cycle_id": cycle_id},
                        error=f"cycle_not_found: {cycle_id}",
                    )
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output={
                        "executor": self.get_executor_name(),
                        "cycle_id": cycle_id,
                        "cycle": result,
                    },
                )

            # 建新周期
            platform = str(params.get("platform") or "").strip()
            account_label = str(params.get("account_label") or params.get("account") or "").strip()
            if not platform or not account_label:
                return ExecutorResult(
                    node_id=node.id,
                    status="failed",
                    output={},
                    error="missing_params: 建养号周期需 platform + account_label",
                )

            rules = params.get("rules")
            cycle = sn.create_cycle(
                context.db,
                tenant_id=context.tenant_id,
                platform=platform,
                account_label=account_label,
                platform_account_id=params.get("platform_account_id"),
                notes=str(params.get("notes") or ""),
                rules=rules if isinstance(rules, dict) else None,
            )
        except Exception as exc:  # noqa: BLE001 — 契约要求失败返回而非抛出
            logger.exception("NurtureExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output={
                "executor": self.get_executor_name(),
                "cycle_id": str((cycle or {}).get("id", "")),
                "platform": platform,
                "cycle": cycle,
                # 新周期默认处于初期，不等于"已养好"——如实标注
                "note": "周期已创建，需后续 advance 推进；当前不代表账号已可用于高频互动",
            },
        )


    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "nurture.create": {
                "desc": "为某平台账号建养号周期（业务链第 7 环）",
                "input": ["platform", "account_label", "platform_account_id", "rules"],
                "output": ["cycle_id", "platform", "cycle"],
                "cost": {"tokens": 0, "seconds": 10},
                "needs_approval": False,
            },
            "nurture.advance": {"desc": "推进既有养号周期", "input": ["cycle_id"]},
        }


ExecutorRegistry.register(NurtureExecutor())
