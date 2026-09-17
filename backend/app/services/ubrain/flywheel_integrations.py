# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P2 外挂槽位：Mem0 双写、PostHog 埋点、n8n 状态（未配置则 no-op）。"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 4.0


def _mem0_url() -> str:
    """_mem0_url。
    :return: 返回处理结果。
    """
    return (os.getenv("MEM0_API_URL") or "").strip().rstrip("/")


def _posthog_host() -> str:
    """_posthog_host。
    :return: 返回处理结果。
    """
    return (os.getenv("POSTHOG_HOST") or "https://us.i.posthog.com").strip().rstrip("/")


def _posthog_key() -> str:
    """_posthog_key。
    :return: 返回处理结果。
    """
    return (os.getenv("POSTHOG_PROJECT_API_KEY") or os.getenv("POSTHOG_API_KEY") or "").strip()


def graphrag_integration_status() -> dict[str, Any]:
    """P2 GraphRAG / Neo4j 占位：默认关闭，仅报告配置是否齐全。"""
    uri = (os.getenv("NEO4J_URI") or "").strip()
    user = (os.getenv("NEO4J_USER") or "").strip()
    password = (os.getenv("NEO4J_PASSWORD") or "").strip()
    enabled_flag = (os.getenv("GRAPHRAG_SYNC_ENABLED") or "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    neo4j_configured = bool(uri and user and password)
    enabled = enabled_flag and neo4j_configured
    return {
        "enabled": enabled,
        "neo4j_configured": neo4j_configured,
        "mode": "disabled" if not enabled else "entities_json_to_neo4j",
        "doc": "docs/出海计/GraphRAG-占位与Neo4j对接.md",
    }


def tavily_integration_status() -> dict[str, Any]:
    """tavily_integration_status。
    :return: 返回处理结果。
    """
    from app.services.geo.tavily_search import tavily_configured
    return {
        "configured": tavily_configured(),
        "mode": "tech_radar_external_search",
    }


def flywheel_integrations_status() -> dict[str, Any]:
    """flywheel_integrations_status。
    :return: 返回处理结果。
    """
    from app.services.geo.headless_rank_probe_service import headless_probe_sidecar_status
    from app.services.crawlers.ecommerce_crawlers_sidecar import ecommerce_crawlers_sidecar_status
    from app.services.analytics.user_action_analytics_sidecar import user_action_analytics_sidecar_status
    from app.services.ubrain.ai_find_customer_sidecar import ai_find_customer_sidecar_status
    from app.services.ubrain.deerflow_sidecar import deerflow_sidecar_status
    mem0 = _mem0_url()
    ph_key = _posthog_key()
    n8n_secret = (os.getenv("N8N_WEBHOOK_SECRET") or "").strip()
    return {
        "graphrag": graphrag_integration_status(),
        "tavily": tavily_integration_status(),
        "deerflow_sidecar": deerflow_sidecar_status(),
        "ai_find_customer_sidecar": ai_find_customer_sidecar_status(),
        "headless_probe_sidecar": headless_probe_sidecar_status(),
        "ecommerce_crawlers_sidecar": ecommerce_crawlers_sidecar_status(),
        "user_action_analytics_sidecar": user_action_analytics_sidecar_status(),
        "mem0": {
            "configured": bool(mem0),
            "endpoint": mem0 or None,
            "mode": "dual_write_on_insight",
        },
        "posthog": {
            "configured": bool(ph_key),
            "host": _posthog_host() if ph_key else None,
            "mode": "capture_on_feedback_and_job",
        },
        "n8n": {
            "configured": bool(n8n_secret),
            "webhook_path": "/api/v1/ubrain/commercial-os/webhook",
            "header": "X-N8N-Webhook-Secret",
            "example": "deploy/examples/n8n/n8n-deerflow-done.json",
        },
    }


def sync_insight_to_mem0(
    *,
    tenant_id: str,
    insight_id: str,
    intent: str,
    title: str,
    summary: str,
    quality_score: float | None = None,
) -> dict[str, Any]:
    """洞察写入 Mem0（本地 DB 已落库后的双写）。"""
    base = _mem0_url()
    if not base:
        return {"synced": False, "reason": "mem0_not_configured"}
    payload = {
        "user_id": str(tenant_id),
        "metadata": {
            "insight_id": insight_id,
            "intent": intent,
            "quality_score": quality_score,
            "source": "commercial_flywheel_os",
        },
        "messages": [
            {"role": "user", "content": f"{title}\n{summary}"[:8000]},
        ],
    }
    headers: dict[str, str] = {"Content-Type": "application/json"}
    api_key = (os.getenv("MEM0_API_KEY") or "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    paths = ("/v1/memories/", "/memories", "/api/memories")
    last_err = ""
    for path in paths:
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.post(f"{base}{path}", json=payload, headers=headers)
            if resp.status_code < 300:
                return {"synced": True, "path": path, "status": resp.status_code}
            last_err = f"{path}:{resp.status_code}"
        except Exception as exc:
            last_err = f"{path}:{exc}"
            logger.debug("mem0 sync %s failed: %s", path, exc)
    return {"synced": False, "reason": last_err or "mem0_request_failed"}


def capture_posthog_event(
    *,
    event: str,
    tenant_id: str,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """飞轮关键事件埋点（反馈同步、任务完成等）。"""
    key = _posthog_key()
    if not key:
        return {"captured": False, "reason": "posthog_not_configured"}
    body = {
        "api_key": key,
        "event": event,
        "distinct_id": str(tenant_id),
        "properties": {
            "product": "commercial_flywheel_os",
            **(properties or {}),
        },
    }
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(f"{_posthog_host()}/capture/", json=body)
        if resp.status_code < 300:
            return {"captured": True, "status": resp.status_code}
        return {"captured": False, "reason": f"http_{resp.status_code}"}
    except Exception as exc:
        logger.debug("posthog capture failed: %s", exc)
        return {"captured": False, "reason": str(exc)[:200]}
