# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Growth Probe Executor — 渠道/支付/收录/健康探针深接（诚实状态）。

    growth_probe.channels     获客渠道 real/mock 状态
    growth_probe.payment      支付沙箱探活（未配置诚实 failed）
    growth_probe.seo_include  URL 收录探针
    growth_probe.mcp_health   Agent Hub MCP 健康
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = {
    "growth_probe.channels": {
        "desc": "获客渠道可用性（real/mock 红标）",
        "input": [],
        "output": ["channels", "mock_count", "real_count"],
        "needs_approval": False,
    },
    "growth_probe.payment": {
        "desc": "支付通道沙箱探活",
        "input": ["provider?"],
        "output": ["provider", "ok", "detail"],
        "needs_approval": False,
    },
    "growth_probe.seo_include": {
        "desc": "URL 是否被搜索引擎收录",
        "input": ["url", "engine?"],
        "output": ["url", "included", "engine"],
        "needs_approval": False,
    },
    "growth_probe.mcp_health": {
        "desc": "MCP 服务健康",
        "input": ["name?"],
        "output": ["name", "health"],
        "needs_approval": False,
    },
}


class GrowthProbeExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "growth_probe"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        cap = (node.capability or "").strip()
        p = dict(node.input or {})
        try:
            if cap in ("growth_probe.channels", "default"):
                return self._channels(node)
            if cap == "growth_probe.payment":
                return self._payment(node, p)
            if cap == "growth_probe.seo_include":
                return self._seo_include(node, p)
            if cap == "growth_probe.mcp_health":
                return self._mcp(node, p)
            return ExecutorResult(node_id=node.id, status="skipped", output={}, error=f"unsupported {cap}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("growth_probe failed %s", cap)
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:300])

    def _channels(self, node) -> ExecutorResult:
        try:
            from app.services.ubrain.channel_status import get_all_channel_statuses

            items = get_all_channel_statuses()
            channels = [
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status,
                    "reason": c.reason,
                    "is_mock": c.status != "real",
                }
                for c in items
            ]
            mock_n = sum(1 for c in channels if c["is_mock"])
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "channels": channels,
                    "mock_count": mock_n,
                    "real_count": len(channels) - mock_n,
                    "hint": "mock/coming_soon 渠道结果不可当真实线索",
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))

    def _payment(self, node, p) -> ExecutorResult:
        provider = str(p.get("provider") or "alipay").lower()
        try:
            from app.services import payment_ops_service as pos

            if provider.startswith("wechat"):
                out = pos.probe_wechat_native() if hasattr(pos, "probe_wechat_native") else None
            else:
                out = pos.probe_alipay_sandbox() if hasattr(pos, "probe_alipay_sandbox") else None
            if out is None:
                return ExecutorResult(
                    node_id=node.id,
                    status="failed",
                    output={"provider": provider, "ok": False},
                    error="payment probe function missing",
                )
            ok = bool(out.get("ok") if isinstance(out, dict) else out)
            if not isinstance(out, dict):
                out = {"ok": ok, "raw": str(out)[:200]}
            # 未配置时诚实 failed
            if not ok or out.get("configured") is False or "not_configured" in str(out.get("status") or ""):
                return ExecutorResult(
                    node_id=node.id,
                    status="failed",
                    output={"provider": provider, "ok": False, "detail": out},
                    error=str(out.get("message") or out.get("detail") or "payment channel not configured")[:200],
                )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={"provider": provider, "ok": True, "detail": out, "executor": self.get_executor_name()},
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={"provider": provider, "ok": False}, error=str(exc)[:200])

    def _seo_include(self, node, p) -> ExecutorResult:
        url = str(p.get("url") or "").strip()
        if not url or not url.startswith("http"):
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing valid url")
        try:
            from app.services.seo.inclusion_probe import probe_url_inclusion

            engine = str(p.get("engine") or "baidu")
            out = probe_url_inclusion(url, engine=engine)
            data = out if isinstance(out, dict) else {"raw": out}
            included = bool(data.get("included") if isinstance(data, dict) else False)
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "url": url,
                    "engine": engine,
                    "included": included,
                    "detail": data,
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:200])

    def _mcp(self, node, p) -> ExecutorResult:
        name = str(p.get("name") or "").strip()
        try:
            from app.services.agent_hub_service import probe_mcp_server_health

            if not name:
                return ExecutorResult(
                    node_id=node.id,
                    status="failed",
                    output={},
                    error="missing mcp name",
                )
            health = probe_mcp_server_health(name=name)
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={"name": name, "health": health, "executor": self.get_executor_name()},
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:200])


ExecutorRegistry.register(GrowthProbeExecutor())
