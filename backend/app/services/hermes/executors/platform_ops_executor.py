# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Platform Ops Executor — 平台运营深接（租户/产品/SEO/通知）。

能力：
    platform_ops.tenant_list      租户列表（真 DB）
    platform_ops.product_catalog  产品/分类摘要（真 DB）
    platform_ops.seo_health       SEO 矩阵配置可读性
    platform_ops.system_health    系统健康探活
    platform_ops.notify_draft     起草站内通知（不自动外发）
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = {
    "platform_ops.tenant_list": {"desc": "列出租户", "input": ["limit?"], "output": ["tenants"]},
    "platform_ops.product_catalog": {"desc": "产品分类摘要", "input": ["limit?"], "output": ["categories"]},
    "platform_ops.seo_health": {"desc": "SEO 关键词/审计可读", "input": [], "output": ["keywords"]},
    "platform_ops.system_health": {"desc": "系统健康", "input": [], "output": ["ok"]},
    "platform_ops.notify_draft": {
        "desc": "起草通知（入库草稿，不自动推送）",
        "input": ["title", "body", "tenant_id?"],
        "output": ["draft_id", "status"],
        "needs_approval": True,
    },
}


class PlatformOpsExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "platform_ops"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        cap = (node.capability or "").strip()
        p = dict(node.input or {})
        try:
            if cap in ("platform_ops.tenant_list", "default"):
                return self._tenants(node, context, p)
            if cap == "platform_ops.product_catalog":
                return self._products(node, context, p)
            if cap == "platform_ops.seo_health":
                return self._seo(node, context, p)
            if cap == "platform_ops.system_health":
                return self._health(node, context)
            if cap == "platform_ops.notify_draft":
                return self._notify_draft(node, context, p)
            return ExecutorResult(node_id=node.id, status="skipped", output={}, error=f"unsupported {cap}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("platform_ops failed %s", cap)
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:300])

    def _tenants(self, node, context, p) -> ExecutorResult:
        if context.db is None:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="db_unavailable")
        try:
            from app.models.tenant import Tenant

            lim = max(1, min(50, int(p.get("limit") or 10)))
            rows = context.db.query(Tenant).limit(lim).all()
            items = [
                {
                    "id": str(getattr(t, "id", "")),
                    "name": getattr(t, "name", "") or "",
                    "domain": getattr(t, "domain", "") or "",
                    "status": getattr(t, "status", "") or "",
                }
                for t in rows
            ]
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={"tenants": items, "count": len(items), "executor": self.get_executor_name()},
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))

    def _products(self, node, context, p) -> ExecutorResult:
        if context.db is None:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="db_unavailable")
        try:
            from app.models.product import Category, Product

            lim = max(1, min(50, int(p.get("limit") or 10)))
            cats = context.db.query(Category).limit(lim).all()
            c_items = [{"id": str(getattr(c, "id", "")), "name": getattr(c, "name", "") or ""} for c in cats]
            try:
                pcount = context.db.query(Product).count()
            except Exception:
                pcount = None
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "categories": c_items,
                    "product_count": pcount,
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))

    def _seo(self, node, context, p) -> ExecutorResult:
        if context.db is None:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="db_unavailable")
        try:
            from app.models.seo import Keyword

            n = context.db.query(Keyword).count()
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={"keywords": n, "executor": self.get_executor_name()},
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))

    def _health(self, node, context) -> ExecutorResult:
        ok = True
        checks = {}
        if context.db is not None:
            try:
                from sqlalchemy import text
                context.db.execute(text("select 1"))
                checks["db"] = True
            except Exception as exc:  # noqa: BLE001
                ok = False
                checks["db"] = False
                checks["db_error"] = str(exc)[:120]
        else:
            checks["db"] = None
        return ExecutorResult(
            node_id=node.id,
            status="succeeded" if ok else "failed",
            output={"ok": ok, "checks": checks, "executor": self.get_executor_name()},
        )

    def _notify_draft(self, node, context, p) -> ExecutorResult:
        title = str(p.get("title") or "").strip()
        body = str(p.get("body") or "").strip()
        if not title or not body:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_title_or_body")
        # 只起草：内存/日志留痕，不自动推送
        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output={
                "draft_id": f"notify-draft-{abs(hash((title, body))) % 10**8:08d}",
                "status": "draft",
                "title": title,
                "note": "草稿已生成，未自动推送（人审后发送）",
                "executor": self.get_executor_name(),
            },
        )


ExecutorRegistry.register(PlatformOpsExecutor())
