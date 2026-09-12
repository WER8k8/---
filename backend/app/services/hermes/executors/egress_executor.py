"""Egress Executor Plugin — 静态 IP 槽位分配 + 指纹环境。

对应业务链第 7 环「分配」：给租户的社媒账号分配**独立静态 IP** 与**指纹环境**，
避免多账号被平台判定关联。

承载实现（已存在，本插件只做契约适配）：
    services/egress_quota_service.auto_assign_slots_for_tenant   ← 按需采购/排队开通
    services/egress_jit_provision_service.process_provision_job  ← 处理单个开通任务
    models/egress.py: EgressEndpoint(IP槽位) / BrowserProfile(指纹环境)

能力：
    egress.assign   —— 为租户分配 IP 槽位
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"egress.assign", "egress.provision", "default"})


class EgressExecutor(BaseExecutor):
    """静态 IP / 指纹环境分配执行器（第三条计费轨的实体操作）。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "egress"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"egress 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})
        try:
            want = int(params.get("count") or 0)
        except (TypeError, ValueError):
            want = 0

        try:
            from app.models.tenant import Tenant
            from app.services.egress_quota_service import (
                auto_assign_slots_for_tenant,
                tenant_egress_summary,
            )

            tenant = (
                context.db.query(Tenant)
                .filter(Tenant.id == context.tenant_id)
                .first()
            )
            if tenant is None:
                return ExecutorResult(
                    node_id=node.id,
                    status="failed",
                    output={},
                    error=f"租户不存在: {context.tenant_id}",
                )

            # count=None 表示补满配额；显式给数则按需分配
            queued = auto_assign_slots_for_tenant(
                context.db, tenant, count=(want or None)
            )
            summary = tenant_egress_summary(context.db, tenant)
        except Exception as exc:  # noqa: BLE001 — 契约要求失败返回而非抛出
            logger.exception("EgressExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = {
            "executor": self.get_executor_name(),
            "queued": queued,
            "quota": summary.get("quota"),
            "assigned": summary.get("assigned"),
            "available": summary.get("available"),
            "summary": summary,
            # 排队≠开通完成：明确标注，供上层判断是否真交付
            "note": "queued 表示已排队开通，非即时可用；实际可用性以 summary.assigned 为准",
        }
        return ExecutorResult(node_id=node.id, status="succeeded", output=output)


    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "egress.assign": {
                "desc": "分配独立静态 IP / 指纹环境槽位（第三条计费轨）",
                "input": ["count"],
                "output": ["queued", "quota", "assigned", "available"],
                "cost": {"tokens": 0, "seconds": 60},
                "needs_approval": False,
            },
            "egress.provision": {"desc": "同 egress.assign（别名）", "input": ["count"]},
        }


ExecutorRegistry.register(EgressExecutor())
