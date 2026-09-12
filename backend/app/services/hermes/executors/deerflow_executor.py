"""DeerFlow Executor Plugin for Hermes Orchestration."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Optional

from app.models.deerflow_job import DeerflowJob
from app.schemas.hermes_orchestration import ExecutorResult, TaskNode
from app.services.deerflow.executor import SubTaskExecutor
from app.services.deerflow.planner import SubTask
from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

# Hermes 能力名 → DeerFlow 内部 intent 名的映射表。
# 为什么需要：DeerFlow 的 _dispatch_by_intent 只认自己那 9 个 intent，
# 而编排图里下发的是 Hermes 能力名（如 seo.optimize）。不加这层翻译，
# 能力名会一路掉进 _exec_generic 兜底分支，2026-09-10 实测正是这样让
# n3 撞上一个外键约束、把整条计划拖崩。映射到已有 intent 才是真接线。
_CAPABILITY_TO_INTENT: Dict[str, str] = {
    "research.deep_run": "keyword_research",
    "seo.optimize": "seo_metadata",
    "content.create": "content_creation",
    "outreach.letter": "outreach_letter",
    "prospect.enrich": "buyer_research",
    "publish.multi": "multi_channel_publish",
    "publish.single": "seo_publish",
}


class DeerflowExecutor(BaseExecutor):
    """Hermes 适配器：将 DeerFlow 9 大子任务执行器纳入 ExecutorRegistry 契约体系。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "deerflow"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        """执行 DeerFlow 节点任务并返回标准 ExecutorResult。"""
        intent = node.capability
        if intent.startswith("deerflow."):
            intent = intent.split(".", 1)[1]
        # 能力名翻译成 DeerFlow intent；不在表里时保留原名（走通用分支）
        intent = _CAPABILITY_TO_INTENT.get(intent, intent)

        params = dict(node.input or {})

        # 构建承载 job（优先查找上下文存在的 job，无则以合成对象承载）
        job = None
        try:
            if context.plan_id:
                job = context.db.query(DeerflowJob).filter(DeerflowJob.id == context.plan_id).first()
        except Exception:
            pass

        if not job:
            # deerflow_jobs 表没有 title 列（2026-09-10 真跑 n3 seo.optimize 时
            # 传 title= 直接 TypeError 整节点失败）。意图与非空列按模型契约给全，
            # job id 用 plan+node 合成，避免同一计划内多节点撞主键。
            job = DeerflowJob(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"hermes:{context.plan_id}:{node.id}")),
                tenant_id=context.tenant_id,
                intent=(intent or node.capability or "hermes_node")[:64],
                status="running",
                payload_json=json.dumps(params, ensure_ascii=False),
            )

        subtask = SubTask(
            id=node.id,
            title=f"Subtask {node.id}: {intent}",
            intent=intent,
            agent_ref=node.sop_ref or "",
            parameters=params,
        )

        executor = SubTaskExecutor(db=context.db, job=job)
        try:
            res = executor.execute_subtask(subtask)
            if res.success:
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output=res.output or {"result": "ok"},
                )
            else:
                return ExecutorResult(
                    node_id=node.id,
                    status="failed",
                    error=res.error or "DeerFlow execution failed",
                    output=res.output or {},
                )
        except Exception as exc:
            logger.exception("DeerflowExecutor run failed: %s", exc)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                error=f"{type(exc).__name__}: {str(exc)}",
            )


    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "research.deep_run": {"desc": "深度研究（DeerFlow 9 意图之一）", "input": ["topic", "depth"]},
            "seo.optimize": {"desc": "SEO/GEO 优化", "input": ["site_url", "product_name"]},
            # G.7：content.create 归 content 执行器主属；DeerFlow 的 AI 内容生成
            # 走同一 capability 名会与 content 撞名触发 verify_executors 冲突 WARN。
            # 映射表 _CAPABILITY_TO_INTENT 保留 content.create→content_creation，
            # 路由行为不变；这里不再对外声明，消除双属（planner 不再把 DeerFlow 当
            # content.create 候选）。DeerFlow 仍以其专属能力（research/seo/outreach…）承接。
        }


ExecutorRegistry.register(DeerflowExecutor())
