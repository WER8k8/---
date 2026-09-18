# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Browser Executor Plugin for Hermes Orchestration.

把既有 browser_runtime（取证/爬取）包成 ExecutorRegistry 插件，
使业务链 Browser Runtime 环节可被任务图调度。

契约：
    node.executor   = "browser"
    node.capability = "browser.scrape" | "browser.screenshot" | "default"
    node.input      = { url?, selector?, wait_ms?, viewport? }
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"browser.scrape", "browser.screenshot", "default"})


class BrowserExecutor(BaseExecutor):
    """Browser Runtime 执行器：网页取证与截图。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "browser"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"browser 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})
        url = str(params.get("url") or params.get("target_url") or "").strip()

        if not url:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_url: browser 节点需提供 url/target_url",
            )

        try:
            from app.services.browser_runtime.runtime import execute as _browser_execute

            # capability → runtime action 映射（runtime 用 extract/screenshot 等裸动作）
            _action = {
                "browser.scrape": "extract",
                "browser.screenshot": "screenshot",
            }.get(capability, str(capability).split(".")[-1])

            rec = await _browser_execute(
                tenant_id=str(context.tenant_id) if context.tenant_id else "hermes",
                actor="hermes:browser",
                action=_action,
                url=url,
                click_target=str(params.get("selector") or "") or None,
                fill_selector=str(params.get("selector") or "") or None,
                db=context.db,
            )
            status = rec.status or "failed"
            if status == "success":
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output={
                        "executor": "browser",
                        "capability": capability,
                        "url": url,
                        "status": "success",
                        "output_summary": rec.output_summary,
                        "output_ref": rec.output_ref,
                        "screenshot_path": rec.screenshot_path,
                        "evidence": {
                            "status": status,
                            "policy_verdict": rec.policy_verdict,
                            "screenshot_size_bytes": rec.screenshot_size_bytes,
                        },
                    },
                )
            # runtime 如实返回 degraded/failed/blocked → 节点如实上报，绝不伪装成功
            _node_status = "degraded" if status == "degraded" else "failed"
            _err = f"{rec.error_code}: {rec.error_message}" if rec.error_code else (rec.error_message or status)
            return ExecutorResult(
                node_id=node.id,
                status=_node_status,
                output={
                    "executor": "browser",
                    "capability": capability,
                    "url": url,
                    "status": status,
                    "error_code": rec.error_code,
                    "error_message": rec.error_message,
                    "policy_verdict": rec.policy_verdict,
                },
                error=_err,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("BrowserExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"{type(exc).__name__}: {exc}")

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "browser.scrape": {
                "desc": "网页取证（抓取 DOM/文本）",
                "input": ["url", "selector", "wait_ms"],
                "output": ["content", "evidence_path"],
                "cost": {"tokens": 0, "seconds": 15},
                "needs_approval": False,
            },
            "browser.screenshot": {
                "desc": "网页截图（全页/viewport）",
                "input": ["url", "viewport", "full_page"],
                "output": ["screenshot_path", "dimensions"],
                "cost": {"tokens": 0, "seconds": 10},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(BrowserExecutor())
