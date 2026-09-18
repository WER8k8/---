# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Inquiry Capture Executor Plugin for Hermes Orchestration.

把既有 `InquiriesUnifiedService.create_public_lead` 包成 ExecutorRegistry
插件，使业务链第 8 步（询盘捕获）可被任务图调度。

契约（见 docs/串联驱动设计-2026-09-10.md §3）：
    node.executor   = "inquiry"
    node.capability = "inquiry.capture" | "default"
    node.input      = { name, email, phone?, message, product?, source_channel? }

设计纪律（对齐项目"不假交付"铁律）：
    · 失败一律返回 status="failed" 并带 error，不抛异常给调用方
    · 不静默吞异常（记录完整堆栈）
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"inquiry.capture", "default"})


class InquiryExecutor(BaseExecutor):
    """询盘捕获执行器：公开线索 → 真实入库。

    复用既有 `InquiriesUnifiedService.create_public_lead`（真实入库），
    不做二次实现，只做契约适配。
    """

    @classmethod
    def get_executor_name(cls) -> str:
        return "inquiry"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"inquiry 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})
        # 兼容多种入参：name / raw_text / message
        name = str(params.get("name") or params.get("contact_name") or "").strip()
        message = str(params.get("message") or params.get("raw_text") or "").strip()
        if not name and message:
            name = "Hermes Inquiry"
        if not name:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_name: 询盘节点需提供 name（或 message/raw_text）",
            )

        if not message:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_message: 询盘节点需提供 message",
            )

        # PG 下 tenant_id 可能需要 UUID
        tenant_id = str(context.tenant_id) if context.tenant_id else ""
        if tenant_id and context.db is not None:
            try:
                from app.services.acquisition.repo import resolve_tenant_uuid

                resolved = resolve_tenant_uuid(context.db, tenant_id)
                if resolved:
                    tenant_id = resolved
            except Exception:
                pass

        try:
            from app.services.inquiries_unified_service import InquiriesUnifiedService

            svc = InquiriesUnifiedService(context.db)
            result = svc.create_public_lead(
                name=name,
                message=message,
                email=params.get("email") or None,
                phone=params.get("phone") or None,
                product=params.get("product") or None,
                source_channel=params.get("source_channel") or params.get("source") or "hermes",
                tenant_id=tenant_id or None,
            )
        except Exception as exc:  # noqa: BLE001 — 契约要求失败返回而非抛出
            logger.exception("InquiryExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = dict(result or {})
        output["executor"] = self.get_executor_name()
        output["inquiry_id"] = output.get("id")
        return ExecutorResult(node_id=node.id, status="succeeded", output=output)

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "inquiry.capture": {
                "desc": "公开询盘线索 → 真实入库（含发现问句注入）",
                "input": ["name", "message", "email", "phone", "product", "source_channel"],
                "output": ["inquiry_id", "subject", "source_channel"],
                "cost": {"tokens": 500, "seconds": 5},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(InquiryExecutor())
