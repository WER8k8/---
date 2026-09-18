# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""全模块业务机器人 — 把「可调度」升成「业务动作」。

契约：
    node.executor   = "biz_bot"
    node.capability = "biz_bot.run" | "biz_bot.list_actions" | "biz_bot.coverage"
    node.input      = { "module": "acquisition", "payload": {} }

目标：每个路由模块都是业务机器人（不是只 surface）。
纪律：真调用服务/真统计；失败 failed；无引擎不报成功。
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = {
    "biz_bot.run": {
        "desc": "全模块业务机器人：优先真业务动作，否则能力面+下一步",
        "input": ["module", "action?", "payload?"],
        "output": ["module", "mode", "result"],
        "needs_approval": False,
    },
    "biz_bot.list_actions": {
        "desc": "列出已注册业务动作模块",
        "input": [],
        "output": ["business_modules", "coverage"],
    },
    "biz_bot.coverage": {
        "desc": "业务机器人覆盖率（相对真实路由模块）",
        "input": [],
        "output": ["route_modules", "registered", "coverage_pct", "all_covered"],
    },
}


class BizBotExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "biz_bot"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def _deep_runner(self, context: ExecutorContext, executor: str, capability: str, payload: dict) -> Any:
        """同步语义的深接调用：真跑已注册执行器，返回 output dict。"""
        ex = ExecutorRegistry.get(executor)
        node = TaskNode(
            id=f"biz-deep-{executor}",
            executor=executor,
            capability=capability,
            input=payload,
        )
        ctx = ExecutorContext(
            db=context.db,
            tenant_id=context.tenant_id,
            plan_id=context.plan_id,
        )
        res = await ex.run(node, ctx)
        return {
            "status": res.status,
            "output": res.output,
            "error": res.error,
        }

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        cap = (node.capability or "biz_bot.run").strip()
        p = dict(node.input or {})
        try:
            from app.services.hermes.biz_bot_actions import (
                MODULE_BUSINESS,
                all_route_modules,
                coverage_report,
                run_module_business,
            )

            if cap in ("biz_bot.list_actions", "biz_bot.coverage"):
                cov = coverage_report()
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output={
                        "business_modules": sorted(MODULE_BUSINESS.keys()),
                        "route_modules": all_route_modules(),
                        "coverage": cov,
                        "all_covered": cov.get("all_covered"),
                        "executor": self.get_executor_name(),
                    },
                )

            module = str(p.get("module") or p.get("target_module") or "").strip()
            if not module:
                return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing module")

            payload = p.get("payload") if isinstance(p.get("payload"), dict) else {
                k: v for k, v in p.items() if k not in ("module", "action", "executor")
            }

            async def deep_runner(ex_name: str, capability: str, deep_payload: dict) -> Any:
                return await self._deep_runner(context, ex_name, capability, deep_payload)

            out = run_module_business(
                module,
                payload=payload,
                db=context.db,
                deep_runner=deep_runner,
            )
            # deep_runner 是 async：run_module_business 同步调用会拿到 coroutine
            if asyncio.iscoroutine(out.get("deep_result")):
                out["deep_result"] = await out["deep_result"]
                out["deep_note"] = f"已调用 {out.get('deep_executor')}.{out.get('deep_capability')}"

            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    **out,
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("biz_bot failed cap=%s", cap)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"biz_bot: {exc}"[:300],
            )


ExecutorRegistry.register(BizBotExecutor())

# 供台账 / 测试
try:
    from app.services.hermes.biz_bot_actions import MODULE_BUSINESS, all_route_modules

    BIZ_BOT_MODULES = sorted(set(list(MODULE_BUSINESS.keys()) + all_route_modules()))
except Exception:  # noqa: BLE001
    BIZ_BOT_MODULES = []
