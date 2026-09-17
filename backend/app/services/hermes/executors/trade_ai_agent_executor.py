# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Trade AI Agent Executor — 接真实适配器（不再返回假数据）。

⚠️ 本文件此前是**纯 mock**：伪造格式类似 `buyerN@<keyword>-intl.com` 的假线索邮箱、
   编造的电话号、以及在**未真实发送**的情况下直接返回 `message_status:"sent"`。
   上述伪造已全部移除。

现在的行为：
    经 `services.adapters.tradeai`（**真实代码级嫁接**，MIT，命名空间隔离）
    调用 vendor 的 `AgentOrchestrator.execute_workflow()`：
      · 找到匹配的 workflow/skill → 真执行，返回真实产出
      · 找不到 → **明确 failed**，并列出当前可用的 workflow/skill（绝不编造）

能力映射（capability → vendor workflow/skill 名，按序匹配）：
    prospect.scrape / prospect_search  → prospect_search / lead_finder
    outreach.whatsapp                  → whatsapp_outreach / whatsapp_send
    outreach.email / cold_email        → email_campaign / cold_email
    inbox.classify                     → inbox_classify / intent_classify

合规提醒（README 原文）：
    「README 声明 MIT，但根目录无 LICENSE 文件——商用合入前必须向作者书面确认
     （总纲 §9.4-1，未完成前不得对外分发含本适配器的版本）」
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

# capability → 候选 workflow/skill 名（按序尝试）
_CAP_TO_TARGETS: dict[str, tuple[str, ...]] = {
    "prospect.scrape": ("prospect_search", "scrape_prospects", "lead_finder"),
    "prospect_search": ("prospect_search", "scrape_prospects", "lead_finder"),
    "scrape_prospects": ("prospect_search", "scrape_prospects", "lead_finder"),
    "prospect.enrich": ("prospect_enrich", "lead_finder"),
    "outreach.whatsapp": ("whatsapp_outreach", "whatsapp_send"),
    "whatsapp_send": ("whatsapp_outreach", "whatsapp_send"),
    "outreach.email": ("email_campaign", "cold_email"),
    "email_campaign": ("email_campaign", "cold_email"),
    "cold_email": ("email_campaign", "cold_email"),
    "inbox.classify": ("inbox_classify", "intent_classify"),
    "intent_classify": ("inbox_classify", "intent_classify"),
}


class TradeAiAgentExecutor(BaseExecutor):
    """Trade AI Agent 执行器（真实适配器，非 mock）。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "trade_ai_agent"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "").lower().strip()
        if capability.startswith("trade_ai."):
            capability = capability.split(".", 1)[1]
        params: dict[str, Any] = dict(node.input or {})

        try:
            from app.services import adapters
            from app.services.adapters import tradeai as taa
        except Exception as exc:  # noqa: BLE001
            logger.exception("TradeAiAgent: 适配器导入失败")
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"adapter_import_failed: {type(exc).__name__}: {exc}",
            )

        # ① 可用性自检
        try:
            available = taa.is_available()
        except Exception as exc:  # noqa: BLE001
            logger.exception("TradeAiAgent: is_available() 异常")
            return ExecutorResult(
                node_id=node.id, status="failed", output={},
                error=f"adapter_unavailable: {exc}",
            )
        if not available:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={"capability": capability},
                error=(
                    "tradeai_adapter_not_loaded: 真实适配器未加载（vendor 未隔离成功或 "
                    "_external/trade-ai-agent 缺失）。**不返回假数据**。"
                ),
            )

        # ② 找到匹配的 workflow/skill
        targets = _CAP_TO_TARGETS.get(capability)
        if not targets:
            return ExecutorResult(
                node_id=node.id, status="skipped", output={},
                error=f"trade_ai_agent 不支持 capability={capability!r}",
            )

        try:
            orch = taa.tenant_orchestrator(context.tenant_id)
            wf_names = {getattr(w, "name", "") for w in orch.list_workflows()}
            skill_names = {getattr(s, "name", "") for s in orch.list_skills()}
        except Exception as exc:  # noqa: BLE001
            logger.exception("TradeAiAgent: 取 orchestrator 失败")
            return ExecutorResult(
                node_id=node.id, status="failed", output={},
                error=f"orchestrator_init_failed: {type(exc).__name__}: {exc}",
            )

        hit = next((t for t in targets if t in wf_names), None)
        if hit is None:
            # 真实适配器在线，但该能力对应的 workflow 尚未注册 —— 如实失败，不编造
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={
                    "capability": capability,
                    "available_workflows": sorted(wf_names),
                    "available_skills": sorted(skill_names),
                },
                error=(
                    f"workflow_not_registered: 未找到 {targets} 中的任何一个。"
                    f"当前已注册 workflows={sorted(wf_names)} skills={sorted(skill_names)}；"
                    "需先在 tradeai 侧注册对应 workflow（不返回假数据）"
                ),
            )

        # ③ 真执行：execute_workflow 是异步生成器，收集全部产出
        try:
            collected: list[dict[str, Any]] = []
            async for chunk in orch.execute_workflow(hit, params):
                if isinstance(chunk, dict):
                    collected.append(chunk)
                    if chunk.get("type") == "error":
                        return ExecutorResult(
                            node_id=node.id,
                            status="failed",
                            output={"workflow": hit, "steps": collected},
                            error=str(chunk.get("error") or "workflow error"),
                        )
        except Exception as exc:  # noqa: BLE001
            logger.exception("TradeAiAgent: 执行 workflow %s 失败", hit)
            return ExecutorResult(
                node_id=node.id, status="failed",
                output={"workflow": hit},
                error=f"{type(exc).__name__}: {exc}",
            )

        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output={
                "executor": self.get_executor_name(),
                "capability": capability,
                "workflow": hit,
                "steps": collected,
                "step_count": len(collected),
            },
        )


    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "prospect.scrape": {
                "desc": "社媒/地图潜客挖掘（走真实 tradeai 适配器；未注册 workflow 即失败）",
                "input": ["keyword", "country", "limit"],
                "output": ["workflow", "steps", "step_count"],
                "cost": {"tokens": 10000, "seconds": 180},
                "needs_approval": False,
            },
            "outreach.whatsapp": {
                "desc": "WhatsApp 触达（真实桥；未接通即失败，不伪造 sent）",
                "input": ["whatsapp", "message", "template_id"],
                "needs_approval": True,
            },
            "outreach.email": {"desc": "冷邮件序列", "input": ["email", "subject", "body"]},
            "inbox.classify": {"desc": "收件箱意图分类", "input": ["message"]},
        }


ExecutorRegistry.register(TradeAiAgentExecutor())
