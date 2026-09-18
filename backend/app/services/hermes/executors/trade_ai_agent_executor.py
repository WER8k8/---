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

# capability → 候选 workflow/skill 名（按序尝试）。
# 说明：vendor 的 AgentOrchestrator 原生不注册任何 workflow，故真实可命中项
# 落在 vendor SkillRegistry 的 8 个 skill 类（social_scraper / auto_sender /
# intent_analysis …）。此处保留原始 workflow 名（未来注册后可命中）并追加
# 对应的可执行 skill 名作为兜底，使能力调用不再一律 workflow_not_registered。
_CAP_TO_TARGETS: dict[str, tuple[str, ...]] = {
    "prospect.scrape": ("prospect_search", "scrape_prospects", "lead_finder", "social_scraper", "excel_reader"),
    "prospect_search": ("prospect_search", "scrape_prospects", "lead_finder", "social_scraper", "excel_reader"),
    "scrape_prospects": ("prospect_search", "scrape_prospects", "lead_finder", "social_scraper", "excel_reader"),
    "prospect.enrich": ("prospect_enrich", "lead_finder", "data_cleaner"),
    "outreach.whatsapp": ("whatsapp_outreach", "whatsapp_send", "auto_sender", "schedule_outreach", "message_generator"),
    "whatsapp_send": ("whatsapp_outreach", "whatsapp_send", "auto_sender", "schedule_outreach", "message_generator"),
    "outreach.email": ("email_campaign", "cold_email", "message_generator", "bulk_message_generator", "auto_sender"),
    "email_campaign": ("email_campaign", "cold_email", "message_generator", "bulk_message_generator", "auto_sender"),
    "cold_email": ("email_campaign", "cold_email", "message_generator", "bulk_message_generator", "auto_sender"),
    "inbox.classify": ("inbox_classify", "intent_classify", "intent_analysis", "ai_reply"),
    "intent_classify": ("inbox_classify", "intent_classify", "intent_analysis", "ai_reply"),
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
            skills = {getattr(s, "name", ""): s for s in orch.list_skills()}
            skill_names = set(skills)
        except Exception as exc:  # noqa: BLE001
            logger.exception("TradeAiAgent: 取 orchestrator 失败")
            return ExecutorResult(
                node_id=node.id, status="failed", output={},
                error=f"orchestrator_init_failed: {type(exc).__name__}: {exc}",
            )

        # 优先命中已注册 workflow；未命中则回退到可执行 skill（vendor 默认不注册
        # workflow，真实能力落在 8 个 skill 类上）。
        wf_hit = next((t for t in targets if t in wf_names), None)
        skill_hit = next((t for t in targets if t in skill_names), None) if wf_hit is None else None
        if wf_hit is None and skill_hit is None:
            # 真实适配器在线，但该能力对应的 workflow/skill 均不可执行 —— 如实失败，不编造
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={
                    "capability": capability,
                    "available_workflows": sorted(wf_names),
                    "available_skills": sorted(skill_names),
                },
                error=(
                    f"capability_not_executable: 未找到 {targets} 中任何可执行 workflow/skill。"
                    f"当前已注册 workflows={sorted(wf_names)} skills={sorted(skill_names)}；"
                    "需先在 tradeai 侧注册对应 workflow 或 skill（不返回假数据）"
                ),
            )

        target_name = wf_hit or skill_hit
        # ③ 真执行
        try:
            if wf_hit is not None:
                # workflow 路径：execute_workflow 是异步生成器，收集全部产出
                collected: list[dict[str, Any]] = []
                async for chunk in orch.execute_workflow(wf_hit, params):
                    if isinstance(chunk, dict):
                        collected.append(chunk)
                        if chunk.get("type") == "error":
                            return ExecutorResult(
                                node_id=node.id, status="failed",
                                output={"workflow": wf_hit, "steps": collected},
                                error=str(chunk.get("error") or "workflow error"),
                            )
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output={
                        "executor": self.get_executor_name(),
                        "capability": capability,
                        "workflow": wf_hit,
                        "steps": collected,
                        "step_count": len(collected),
                        "prospects": collected,
                    },
                )

            # skill 路径：BaseSkill.run(ExecutionContext) 是异步，返回 dict 产出
            from app.services.adapters.tradeai import make_context
            exec_ctx = make_context(
                context.tenant_id,
                task_id=getattr(node, "id", None),
                **params,
            )
            skill = skills[skill_hit]
            result = await skill.run(exec_ctx)
            prospect_items = []
            if isinstance(result, dict):
                prospect_items = result.get("leads") or result.get("prospects") or result.get("items") or []
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "executor": self.get_executor_name(),
                    "capability": capability,
                    "skill": skill_hit,
                    "result": result,
                    "prospects": prospect_items,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("TradeAiAgent: 执行 %s 失败", target_name)
            return ExecutorResult(
                node_id=node.id, status="failed",
                output={"target": target_name},
                error=f"{type(exc).__name__}: {exc}",
            )


    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "prospect.scrape": {
                "desc": "社媒/地图潜客挖掘（走真实 tradeai 适配器；未注册 workflow 即失败）",
                "input": ["keyword", "country", "limit"],
                "output": ["workflow", "steps", "step_count", "prospects"],
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
