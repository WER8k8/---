# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Data Ops Executor — 分析/通知/域名深接。

    data_ops.content_stats   内容/询盘等基础统计（真 DB）
    data_ops.notify_draft    站内通知草稿入库（不自动外发）
    data_ops.domain_resolve  域名解析租户（真 DB）
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

# 落库不可用时的草稿内存落点（degraded 兜底，非持久化真相源）
_DRAFT_MEMO: dict[str, dict[str, Any]] = {}
_DRAFT_MEMO_SEQ = 0


def _memoize_draft(title: str, body: str, tenant_id: str) -> str:
    global _DRAFT_MEMO_SEQ
    _DRAFT_MEMO_SEQ += 1
    memo_id = f"draft-memo-{_DRAFT_MEMO_SEQ:06d}"
    _DRAFT_MEMO[memo_id] = {"title": title, "body": body, "tenant_id": tenant_id, "persisted": False}
    return memo_id

_CAPS = {
    "data_ops.content_stats": {
        "desc": "内容/询盘基础统计",
        "input": [],
        "output": ["stats"],
    },
    "data_ops.notify_draft": {
        "desc": "站内通知草稿（人审后发送）",
        "input": ["user_id?", "title", "body", "tenant_id?"],
        "output": ["status", "title"],
        "needs_approval": True,
    },
    "data_ops.domain_resolve": {
        "desc": "按域名解析租户",
        "input": ["host"],
        "output": ["host", "tenant_id", "found"],
    },
}


class DataOpsExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "data_ops"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        cap = (node.capability or "").strip()
        p = dict(node.input or {})
        try:
            if cap in ("data_ops.content_stats", "default"):
                return self._stats(node, context)
            if cap == "data_ops.notify_draft":
                return self._notify(node, context, p)
            if cap == "data_ops.domain_resolve":
                return self._domain(node, context, p)
            return ExecutorResult(node_id=node.id, status="skipped", output={}, error=f"unsupported {cap}")
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:300])

    def _stats(self, node, context) -> ExecutorResult:
        if context.db is None:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="db_unavailable")
        try:
            from sqlalchemy import text
            from app.services.acquisition import ops_card_store

            stats: dict[str, Any] = {}
            for key, sql in (
                ("inquiries", "select count(*) from inquiries"),
                ("products", "select count(*) from products"),
                ("tenants", "select count(*) from tenants"),
                ("content_pages", "select count(*) from content_pages"),
            ):
                try:
                    stats[key] = int(context.db.execute(text(sql)).scalar() or 0)
                except Exception:
                    stats[key] = None
            cards = list(ops_card_store._by_inquiry.values())
            stats["ops_cards"] = len(cards)
            stats["ops_won"] = sum(1 for c in cards if getattr(c, "stage", "") == "won")
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={"stats": stats, "source": "pg+ops_memory", "executor": self.get_executor_name()},
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))

    def _notify(self, node, context, p) -> ExecutorResult:
        title = str(p.get("title") or "").strip()
        body = str(p.get("body") or "").strip()
        if not title or not body:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_title_or_body")
        # 优先真库草稿；落库不可用/失败则如实 degraded（草稿进内存，绝不假报已保存）
        draft_id = None
        persist_error = None
        if context.db is not None:
            try:
                from app.models.notification import Notification  # type: ignore
                from app.services.acquisition.repo import resolve_tenant_uuid

                tid = resolve_tenant_uuid(context.db, p.get("tenant_id") or context.tenant_id or "")
                n = Notification(
                    user_id=str(p.get("user_id") or "") or None,
                    title=title,
                    content=body,
                    notification_type="system",
                    is_read=False,
                )
                if tid and hasattr(n, "tenant_id"):
                    n.tenant_id = tid
                context.db.add(n)
                context.db.commit()
                draft_id = str(getattr(n, "id", "") or "")
            except Exception as exc:  # noqa: BLE001
                try:
                    context.db.rollback()
                except Exception:
                    pass
                persist_error = f"{type(exc).__name__}: {exc}"
        else:
            persist_error = "db_unavailable"

        if draft_id:
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "status": "draft_saved",
                    "draft_id": draft_id,
                    "title": title,
                    "note": "通知草稿已入库，未自动推送（须人审）",
                    "executor": self.get_executor_name(),
                },
            )
        # 落库不可用/失败 → 草稿仅存内存，如实 degraded，绝不伪装已保存
        memo_id = _memoize_draft(title, body, str(p.get("tenant_id") or ""))
        return ExecutorResult(
            node_id=node.id,
            status="degraded",
            output={
                "status": "draft_memory_only",
                "draft_id": memo_id,
                "title": title,
                "note": "通知草稿入库失败，仅存内存（未自动推送，须人审）",
                "executor": self.get_executor_name(),
            },
            error=f"通知草稿未入库: {persist_error}",
        )

    def _domain(self, node, context, p) -> ExecutorResult:
        host = str(p.get("host") or "").strip().lower()
        if not host:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_host")
        if context.db is None:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="db_unavailable")
        try:
            from sqlalchemy import text

            row = context.db.execute(
                text(
                    "select id::text, name, domain from tenants "
                    "where domain = :h or custom_domains like :like limit 1"
                ),
                {"h": host, "like": f"%{host}%"},
            ).mappings().first()
            if not row:
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output={"host": host, "tenant_id": None, "found": False, "executor": self.get_executor_name()},
                )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "host": host,
                    "tenant_id": row.get("id"),
                    "tenant_name": row.get("name") or "",
                    "found": True,
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))


ExecutorRegistry.register(DataOpsExecutor())
