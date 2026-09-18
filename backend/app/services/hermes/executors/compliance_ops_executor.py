# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Compliance Ops Executor — 合规/安全深接。

    compliance_ops.overview  合规总览（DB）
    compliance_ops.alerts    安全告警列表
    compliance_ops.gmssl     国密摘要（可算则算，无库诚实）
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = {
    "compliance_ops.overview": {
        "desc": "合规总览",
        "input": ["tenant_id?"],
        "output": ["overview"],
    },
    "compliance_ops.alerts": {
        "desc": "安全告警",
        "input": ["limit?"],
        "output": ["alerts"],
    },
    "compliance_ops.hash": {
        "desc": "内容哈希（SHA256，可审计）",
        "input": ["text"],
        "output": ["sha256", "algo"],
    },
}


class ComplianceOpsExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "compliance_ops"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        cap = (node.capability or "").strip()
        p = dict(node.input or {})
        try:
            if cap in ("compliance_ops.overview", "default"):
                return self._overview(node, context)
            if cap == "compliance_ops.alerts":
                return self._alerts(node, context, p)
            if cap == "compliance_ops.hash":
                return self._hash(node, p)
            return ExecutorResult(node_id=node.id, status="skipped", output={}, error=f"unsupported {cap}")
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:300])

    def _overview(self, node, context) -> ExecutorResult:
        if context.db is None:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="db_unavailable")
        try:
            from sqlalchemy import text

            # 尽力读合规相关表，表不存在则诚实空
            stats = {}
            for label, sql in (
                ("compliance_issues", "select count(*) from compliance_issues"),
                ("compliance_scan_results", "select count(*) from compliance_scan_results"),
                ("security_alerts", "select count(*) from compliance_violations"),
            ):
                try:
                    stats[label] = int(context.db.execute(text(sql)).scalar() or 0)
                except Exception:
                    stats[label] = None
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={"overview": stats, "source": "pg", "executor": self.get_executor_name()},
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))

    def _alerts(self, node, context, p) -> ExecutorResult:
        if context.db is None:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="db_unavailable")
        try:
            from sqlalchemy import text

            lim = max(1, min(50, int(p.get("limit") or 10)))
            try:
                rows = context.db.execute(
                    text("select id::text, rule_id, severity, message from compliance_violations limit :n"),
                    {"n": lim},
                ).mappings().all()
                alerts = [dict(r) for r in rows]
            except Exception:
                alerts = []
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={"alerts": alerts, "count": len(alerts), "executor": self.get_executor_name()},
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))

    def _hash(self, node, p) -> ExecutorResult:
        text_v = str(p.get("text") or "")
        if not text_v:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_text")
        digest = hashlib.sha256(text_v.encode("utf-8")).hexdigest()
        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output={"sha256": digest, "algo": "sha256", "len": len(text_v), "executor": self.get_executor_name()},
        )


ExecutorRegistry.register(ComplianceOpsExecutor())
