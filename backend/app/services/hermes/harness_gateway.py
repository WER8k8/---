# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DeepSeek Harness Gateway —— 最外层意图入口（接真实拆解器）。

⚠️ 本文件此前是**桩**：`intent` 硬编码为 `"inferred_from_harness"`、
   推理逻辑全是注释掉的 TODO，`process_inbound_webhook` 直接返回一句
   硬编码字符串而不做任何事。另有一个隐藏 bug：`event_id` 用
   `str(hash(raw_text))[:8]` 生成，而 Python 的 `hash()` 受 PYTHONHASHSEED 影响
   **每次进程重启结果都不同** → 同一请求的 event_id 不稳定，幂等失效。

现在的行为：把意图交给真实拆解器 `services/hermes/planner_service.decompose()`，
产出可执行的 `TaskGraph`（L1 模板 / L2 LLM / L3 兜底，带三道安全阀）。
本模块只做「入口适配」，不重复实现拆解逻辑。
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.schemas.hermes_orchestration import IntentEvent, TaskGraph

logger = logging.getLogger(__name__)


class HarnessGateway:
    """租户侧最外层意图入口。"""

    def __init__(self, db: Session):
        self.db = db

    async def ingest_user_intent(
        self,
        tenant_id: str,
        channel: str,
        raw_text: str,
        context: Optional[Dict[str, Any]] = None,
        *,
        intent: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> IntentEvent:
        """把原始输入归一化成 `IntentEvent`（比自由文本更结构化的上游可直接传 intent）。

        :param intent: 上游已知的高层意图（如 generate_site）；不传则用 raw_text，
                       交由 planner 的关键词/LLM 匹配判定。
        """
        text = (raw_text or "").strip()
        if not tenant_id:
            raise ValueError("tenant_id 必填（多租户隔离红线）")
        if not text and not intent:
            raise ValueError("raw_text 与 intent 至少提供一个")

        event = IntentEvent(
            # uuid 而非 hash()：保证跨进程稳定且唯一（原实现用 hash 是 bug）
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            tenant_id=str(tenant_id),
            channel=channel or "web",
            intent=(intent or text),
            payload={**(payload or {}), "raw_input": text},
            context=context or {},
        )
        logger.info(
            "HarnessGateway: intent 归一化 tenant=%s channel=%s event=%s",
            tenant_id, event.channel, event.event_id,
        )
        return event

    async def plan(
        self,
        tenant_id: str,
        channel: str,
        raw_text: str,
        context: Optional[Dict[str, Any]] = None,
        *,
        intent: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> tuple[TaskGraph, str]:
        """归一化 → 拆解，返回 (任务图, 图来源)。来源 ∈ L1_template / L2_llm / L3_minimal。"""
        from app.services.hermes.planner_service import decompose

        event = await self.ingest_user_intent(
            tenant_id, channel, raw_text, context, intent=intent, payload=payload
        )
        graph, source = await decompose(event, self.db)
        logger.info(
            "HarnessGateway: 拆解完成 source=%s nodes=%d plan=%s",
            source, len(graph.nodes), graph.plan_id,
        )
        return graph, source


async def process_inbound_webhook(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
    """n8n / 外部 webhook 入站入口。

    期望 payload 至少含：tenant_id、text（或 intent）。
    返回真实拆解结果；缺少必填字段即**明确抛错**，不再返回硬编码字符串。
    """
    tenant_id = str(payload.get("tenant_id") or "").strip()
    text = str(payload.get("text") or payload.get("message") or "").strip()
    intent = payload.get("intent")
    if not tenant_id:
        raise ValueError("webhook 入站缺 tenant_id，拒绝处理（多租户隔离红线）")
    if not text and not intent:
        raise ValueError("webhook 入站缺 text / intent，无法拆解")

    gateway = HarnessGateway(db)
    graph, source = await gateway.plan(
        tenant_id=tenant_id,
        channel=str(payload.get("channel") or "n8n"),
        raw_text=text,
        context=payload.get("context") if isinstance(payload.get("context"), dict) else None,
        intent=str(intent) if intent else None,
        payload=payload.get("payload") if isinstance(payload.get("payload"), dict) else None,
    )
    return {
        "ok": True,
        "plan_id": graph.plan_id,
        "graph_source": source,
        "node_count": len(graph.nodes),
    }
