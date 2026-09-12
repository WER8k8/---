"""官方 DeerFlow 2.0 旁路：可选 HTTP 研究服务，失败则回退本机 Lite。

DeerFlow 2.0 是字节跳动开源的超级智能体框架，基于 LangGraph + LangChain 构建。
核心特性：子 Agent 编排、Docker 沙箱执行、Markdown Skills 系统、长期记忆。

架构：
- Gateway API（端口 8001）：REST API 网关
- LangGraph Server（端口 2024）：Agent 运行时引擎
- Nginx（端口 2026）：统一访问入口
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 120.0


def sidecar_base_url() -> str:
    """sidecar_base_url。
    :return: 返回处理结果。
    """
    return (os.getenv("DEERFLOW_SIDECAR_URL") or "").strip().rstrip("/")


def deerflow_version() -> str:
    """deerflow_version。
    :return: 返回处理结果。
    """
    return (os.getenv("DEERFLOW_VERSION") or "1.0").strip()


def is_deerflow_v2() -> bool:
    """is_deerflow_v2。
    :return: 返回处理结果。
    """
    version = deerflow_version()
    return version.startswith("2") or version.startswith("2.")


def deerflow_gateway_url() -> str:
    """deerflow_gateway_url。
    :return: 返回处理结果。
    """
    return (os.getenv("DEERFLOW_GATEWAY_URL") or "").strip().rstrip("/")


def deerflow_langgraph_url() -> str:
    """deerflow_langgraph_url。
    :return: 返回处理结果。
    """
    return (os.getenv("DEERFLOW_LANGGRAPH_URL") or "").strip().rstrip("/")


def deerflow_sidecar_status() -> dict[str, Any]:
    """deerflow_sidecar_status。
    :return: 返回处理结果。
    """
    base = sidecar_base_url()
    version = deerflow_version()
    out: dict[str, Any] = {
        "configured": bool(base),
        "url": base or None,
        "version": version,
        "is_v2": is_deerflow_v2(),
        "healthy": None,
        "detail": None,
    }
    if not base:
        out["fallback"] = "deerflow_lite_in_process"
        return out

    secret = (os.getenv("DEERFLOW_SIDECAR_SECRET") or "").strip()
    headers: dict[str, str] = {}
    if secret:
        headers["Authorization"] = f"Bearer {secret}"

    if is_deerflow_v2():
        health_paths = (
            "/health",
            "/api/health",
            "/v1/health",
            "/api/v1/health",
        )
    else:
        health_paths = ("/health", "/api/health", "/v1/health")

    for path in health_paths:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{base}{path}", headers=headers)
            if resp.status_code < 300:
                out["healthy"] = True
                out["health_path"] = path
                try:
                    health_data = resp.json()
                    if isinstance(health_data, dict):
                        out["version_info"] = health_data.get("version")
                        out["services"] = health_data.get("services")
                except Exception:
                    pass
                return out
            out["detail"] = f"{path}: HTTP {resp.status_code}"
        except Exception as exc:
            out["detail"] = str(exc)[:200]

    out["healthy"] = False
    out["fallback"] = "deerflow_lite_in_process"
    return out


def fetch_sidecar_research(*, tenant_id: str, message: str) -> dict[str, Any] | None:
    """调用旁路 DeerFlow；返回与 market_research 任务兼容的 result dict。"""
    base = sidecar_base_url()
    if not base:
        return None

    headers: dict[str, str] = {"Content-Type": "application/json"}
    secret = (os.getenv("DEERFLOW_SIDECAR_SECRET") or "").strip()
    if secret:
        headers["Authorization"] = f"Bearer {secret}"

    if is_deerflow_v2():
        return _fetch_v2_research(base=base, headers=headers, tenant_id=tenant_id, message=message)

    return _fetch_v1_research(base=base, headers=headers, tenant_id=tenant_id, message=message)


def _fetch_v1_research(*, base: str, headers: dict[str, str], tenant_id: str, message: str) -> dict[str, Any] | None:
    """DeerFlow 1.x 研究接口"""
    payload = {"tenant_id": str(tenant_id), "message": message}
    paths = ("/v1/research", "/api/research", "/research")
    for path in paths:
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.post(f"{base}{path}", json=payload, headers=headers)
            if resp.status_code >= 300:
                continue
            data = resp.json()
            if isinstance(data, dict) and "data" in data:
                data = data["data"]
            if not isinstance(data, dict):
                continue
            if data.get("research_brief") or data.get("accio_actions"):
                data.setdefault("mode", "deerflow_sidecar")
                return data
            if data.get("result") and isinstance(data["result"], dict):
                inner = data["result"]
                inner.setdefault("mode", "deerflow_sidecar")
                return inner
        except Exception as exc:
            logger.info("deerflow v1 sidecar %s failed: %s", path, exc)
    return None


def _fetch_v2_research(*, base: str, headers: dict[str, str], tenant_id: str, message: str) -> dict[str, Any] | None:
    """DeerFlow 2.0 研究接口 - 使用 Gateway API"""
    gateway_url = deerflow_gateway_url() or base
    thread_payload = {
        "tenant_id": str(tenant_id),
        "message": message,
        "skill": "deep-search",
        "mode": "ultra",
    }
    paths = (
        "/v1/chat",
        "/api/v1/chat",
        "/chat/completions",
        "/v1/research",
        "/api/v1/research",
    )
    for path in paths:
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.post(f"{gateway_url}{path}", json=thread_payload, headers=headers)
            if resp.status_code >= 300:
                continue
            data = resp.json()
            if isinstance(data, dict):
                if data.get("research_brief") or data.get("accio_actions"):
                    data.setdefault("mode", "deerflow_sidecar_v2")
                    return data
                if data.get("content") and isinstance(data["content"], str):
                    return {
                        "mode": "deerflow_sidecar_v2",
                        "research_brief": {
                            "executive_summary": data["content"],
                            "category": "market_research",
                        },
                        "accio_actions": [],
                        "executive_summary": data["content"],
                    }
                if data.get("result") and isinstance(data["result"], dict):
                    inner = data["result"]
                    inner.setdefault("mode", "deerflow_sidecar_v2")
                    return inner
        except Exception as exc:
            logger.info("deerflow v2 sidecar %s failed: %s", path, exc)

    return _try_langgraph_research(base=base, headers=headers, tenant_id=tenant_id, message=message)


def _try_langgraph_research(*, base: str, headers: dict[str, str], tenant_id: str, message: str) -> dict[str, Any] | None:
    """尝试通过 LangGraph Server 接口获取研究结果"""
    langgraph_url = deerflow_langgraph_url()
    if not langgraph_url:
        return None

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            create_resp = client.post(
                f"{langgraph_url}/threads",
                json={"configurable": {"tenant_id": str(tenant_id)}},
                headers=headers,
            )
        if create_resp.status_code >= 300:
            return None

        thread_data = create_resp.json()
        thread_id = thread_data.get("thread_id")
        if not thread_id:
            return None

        with httpx.Client(timeout=_TIMEOUT) as client:
            run_resp = client.post(
                f"{langgraph_url}/threads/{thread_id}/runs",
                json={
                    "input": {"message": message},
                    "configurable": {"tenant_id": str(tenant_id)},
                },
                headers=headers,
            )
        if run_resp.status_code >= 300:
            return None

        run_data = run_resp.json()
        run_id = run_data.get("run_id")
        import time
        for _ in range(60):
            time.sleep(2)
            with httpx.Client(timeout=10.0) as client:
                status_resp = client.get(
                    f"{langgraph_url}/threads/{thread_id}/runs/{run_id}",
                    headers=headers,
                )
            if status_resp.status_code >= 300:
                continue
            status_data = status_resp.json()
            if status_data.get("status") == "completed":
                return {
                    "mode": "deerflow_sidecar_v2_langgraph",
                    "research_brief": {
                        "executive_summary": status_data.get("output", {}).get("summary", message),
                        "category": "market_research",
                    },
                    "accio_actions": [],
                    "executive_summary": status_data.get("output", {}).get("summary", message),
                }
            if status_data.get("status") in ("failed", "cancelled"):
                break

    except Exception as exc:
        logger.info("deerflow v2 langgraph research failed: %s", exc)

    return None