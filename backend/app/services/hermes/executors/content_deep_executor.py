# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Content Deep Executor — SEO/内容深接（真服务 + 诚实降级）。

    content_deep.seo_meta      生成 SEO 元数据（模板/degraded 如实标注）
    content_deep.acquisition   内容→询盘归因挂接
    content_deep.knowledge     知识队列待办摘要
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = {
    "content_deep.seo_meta": {
        "desc": "SEO 元数据（degraded 如实标记）",
        "input": ["product_name", "industry?"],
        "output": ["meta", "degraded"],
    },
    "content_deep.acquisition": {
        "desc": "内容 ID 挂询盘归因",
        "input": ["content_id", "inquiry_id", "tenant_id?"],
        "output": ["linked", "content_id", "inquiry_id"],
    },
    "content_deep.knowledge": {
        "desc": "合规知识待读摘要",
        "input": ["tenant_id?"],
        "output": ["pending", "next", "plain_summary"],
    },
}


class ContentDeepExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "content_deep"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        cap = (node.capability or "").strip()
        p = dict(node.input or {})
        try:
            if cap in ("content_deep.seo_meta", "default"):
                return self._seo_meta(node, p)
            if cap == "content_deep.acquisition":
                return self._acquisition(p, node)
            if cap == "content_deep.knowledge":
                return self._knowledge(p, node)
            return ExecutorResult(node_id=node.id, status="skipped", output={}, error=f"unsupported {cap}")
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:300])

    def _seo_meta(self, node, p) -> ExecutorResult:
        name = str(p.get("product_name") or p.get("product") or "").strip()
        if not name:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_product_name")
        try:
            from app.services.ai_site_engine import AiSiteEngine  # type: ignore

            eng = AiSiteEngine()
            meta = eng.generate_seo_metadata(name, str(p.get("industry") or ""))
            # 诚实：静态模板/无 Key 时 degraded
            degraded = True
            if isinstance(meta, dict):
                degraded = bool(meta.get("degraded", True))
                # 若有 title/description 且非空，仍标记 degraded 可能为模板
                if meta.get("ai_generated") is True:
                    degraded = False
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "meta": meta if isinstance(meta, dict) else {"raw": meta},
                    "degraded": degraded,
                    "note": "SEO 元数据为模板/降级结果时请人工润色" if degraded else "AI 生成",
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"seo_meta: {exc}")

    def _acquisition(self, p, node) -> ExecutorResult:
        cid = str(p.get("content_id") or "").strip()
        iid = str(p.get("inquiry_id") or "").strip()
        if not cid or not iid:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing content_id/inquiry_id")
        try:
            from app.services.acquisition.growth_ops import content_attr_store

            out = content_attr_store.link_inquiry(
                content_id=cid,
                inquiry_id=iid,
                tenant_id=str(p.get("tenant_id") or "demo"),
            )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={**out, "executor": self.get_executor_name()},
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))

    def _knowledge(self, p, node) -> ExecutorResult:
        try:
            from app.services.acquisition.knowledge_queue import knowledge_queue_store

            rep = knowledge_queue_store.report(tenant_id=str(p.get("tenant_id") or "demo"))
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "pending": rep.get("pending_count"),
                    "next": rep.get("next_item"),
                    "plain_summary": rep.get("plain_summary"),
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))


ExecutorRegistry.register(ContentDeepExecutor())
