# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Site Builder Executor Plugin for Hermes Orchestration.

把已有的建站实现（`hermes_task_bridge._run_site_build` 所依赖的
`run_ai_site_builder_v1`）包成 ExecutorRegistry 插件，使其可被任务图调度。

契约（见 docs/串联驱动设计-2026-09-10.md §3）：
    node.executor    = "site_builder"
    node.capability  = "site.generate" | "site.build" | "default"
    node.input       = { product_name, company_name?, product_images?, auto_save?, use_ai? }
    node.input_from  = {"product_images": "n1.output.urls"}  ← 由 advance_plan 解析后并入 input

设计纪律（对齐项目"不假交付"铁律）：
    · 结果里的 `source` 原样透出，不篡改降级路径的标记
    · 失败一律返回 status="failed" 并带 error，不抛异常给调用方
    · 不静默吞异常（记录完整堆栈）
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

# 本执行器承接的能力名（node.capability 命中其一即执行）
_SUPPORTED_CAPABILITIES = frozenset({"site.generate", "site.build", "default"})


class SiteBuilderExecutor(BaseExecutor):
    """建站执行器：产品图 + 需求 → 多语独立站。

    复用既有 `run_ai_site_builder_v1`（真实实现，含 ECC 设计技能与 i18n），
    不做二次实现，只做契约适配。
    """

    @classmethod
    def get_executor_name(cls) -> str:
        return "site_builder"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"site_builder 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})
        product_name = str(
            params.get("product_name") or params.get("message") or ""
        ).strip()
        if not product_name:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_product: 建站节点需提供 product_name（或 message）",
            )

        company_name = str(params.get("company_name") or "").strip()
        if not company_name:
            company_name = self._resolve_company_name(context)

        raw_images = params.get("product_images") or params.get("productImages") or []
        # input_from 解析后可能是单个 URL 字符串，统一成 list
        if isinstance(raw_images, str):
            raw_images = [raw_images] if raw_images else []
        product_images = raw_images if isinstance(raw_images, list) else []

        auto_save = self._as_bool(params.get("auto_save"), default=True)
        use_ai = self._as_bool(params.get("use_ai"), default=True)

        persist_fn = None
        if auto_save:
            persist_fn = self._resolve_persist_fn()

        try:
            from app.services.hermes.site_build_workflow import run_ai_site_builder_v1

            result = await run_ai_site_builder_v1(
                context.db,
                tenant_id=context.tenant_id,
                product_name=product_name,
                company_name=company_name,
                auto_save=auto_save,
                use_ai=use_ai,
                persist_fn=persist_fn,
                product_images=product_images,
            )
        except Exception as exc:  # noqa: BLE001 — 契约要求失败返回而非抛出
            logger.exception("SiteBuilderExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = dict(result or {})
        output["executor"] = self.get_executor_name()
        output["product_name"] = product_name
        # 透出降级/来源标记，供上层判定是否"真交付"（不篡改）
        output.setdefault("simulated", bool(output.get("source") in ("mock", "fallback")))
        return ExecutorResult(node_id=node.id, status="succeeded", output=output)

    # ── 内部工具 ────────────────────────────────────────────
    def _resolve_company_name(self, context: ExecutorContext) -> str:
        """未显式给公司名时，回落取租户名。取不到不报错，留给下游兜底。"""
        try:
            from app.models.tenant import Tenant

            tenant = (
                context.db.query(Tenant)
                .filter(Tenant.id == context.tenant_id)
                .first()
            )
            return tenant.name if tenant else ""
        except Exception:  # noqa: BLE001 — 公司名非必需，失败不阻断
            logger.warning("SiteBuilderExecutor: 取租户名失败 tenant=%s", context.tenant_id)
            return ""

    @staticmethod
    def _resolve_persist_fn():
        """自动保存钩子；模块缺失时返回 None（不阻断建站）。"""
        try:
            from app.services.tenant_site_persistence import persist_tenant_site_content

            return persist_tenant_site_content
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _as_bool(value: Any, *, default: bool) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() not in ("0", "false", "no", "off", "")
        return bool(value)


    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "site.generate": {
                "desc": "产品图 + 需求 → 多语独立站（含 ECC 设计技能与 i18n）",
                "input": ["product_name", "product_images", "company_name", "auto_save"],
                "output": ["site_content", "reply", "source", "saved"],
                "cost": {"tokens": 50000, "seconds": 600},
                "needs_approval": False,
            },
            "site.build": {"desc": "同 site.generate（别名）", "input": ["product_name"]},
        }


ExecutorRegistry.register(SiteBuilderExecutor())
