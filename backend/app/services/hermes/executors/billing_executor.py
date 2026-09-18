# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Billing Executor Plugin for Hermes Orchestration.

把既有 billing services（meter_event / subscription_countdown）包成
ExecutorRegistry 插件，使业务链计费环节可被任务图调度。

契约：
    node.executor   = "billing"
    node.capability = "billing.meter" | "billing.invoice" | "default"
    node.input      = { tenant_id?, event_type?, amount?, product? }
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"billing.meter", "billing.invoice", "default"})


class BillingExecutor(BaseExecutor):
    """计费执行器：计量事件记录 / 发票生成。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "billing"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"billing 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})

        try:
            if capability in ("billing.meter", "default"):
                from app.services.billing.meter_event import record_meter_event

                event_type = str(params.get("event_type") or params.get("action") or "ai_call").strip()
                result = record_meter_event(
                    context.db,
                    tenant_id=str(context.tenant_id) if context.tenant_id else None,
                    event_type=event_type,
                    amount=int(params.get("amount") or params.get("tokens_used") or 1),
                )
            else:
                from app.services.billing.meter_event import record_meter_event

                result = record_meter_event(
                    context.db,
                    tenant_id=str(context.tenant_id) if context.tenant_id else None,
                    event_type="invoice",
                    amount=int(params.get("amount") or 0),
                )
        except (ImportError, AttributeError) as exc:
            # billing service 未接线 → 如实 degraded，绝不伪装已计量 succeeded
            return ExecutorResult(
                node_id=node.id,
                status="degraded",
                output={
                    "executor": "billing",
                    "capability": capability,
                    "status": "metering_not_wired",
                    "degraded": True,
                    "note": f"billing service 未接线，未计量: {type(exc).__name__}",
                },
                error=f"billing service 未接线: {type(exc).__name__}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("BillingExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"{type(exc).__name__}: {exc}")

        output = dict(result or {})
        output["executor"] = "billing"
        output["capability"] = capability
        return ExecutorResult(node_id=node.id, status="succeeded", output=output)

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "billing.meter": {
                "desc": "计量事件记录（AI调用/静态IP/指纹槽位消耗）",
                "input": ["event_type", "amount", "tenant_id"],
                "output": ["event_id", "balance_after"],
                "cost": {"tokens": 0, "seconds": 2},
                "needs_approval": False,
            },
            "billing.invoice": {
                "desc": "生成计费发票（订阅/用量/加购）",
                "input": ["amount", "product", "tenant_id"],
                "output": ["invoice_id", "total"],
                "cost": {"tokens": 0, "seconds": 3},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(BillingExecutor())
