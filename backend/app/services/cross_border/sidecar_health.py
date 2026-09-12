"""Sidecar 健康探测 — mock/reference 不得计为已配置。"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)

_MOCK_MODES = frozenset({"mock", "reference", "stub", "demo"})


def probe_sidecar_health(base_url: str, *, timeout_sec: float = 5.0) -> dict[str, Any]:
    """GET /api/youding/health；失败或 mock 模式返回 ok=False。"""
    base = (base_url or "").strip().rstrip("/")
    if not base:
        return {"ok": False, "reason": "empty_url"}
    url = urljoin(base + "/", "/api/youding/health")
    try:
        with httpx.Client(timeout=timeout_sec, follow_redirects=True) as client:
            resp = client.get(url)
        if resp.status_code != 200:
            return {"ok": False, "reason": f"http_{resp.status_code}", "url": url}
        data = resp.json() if resp.content else {}
        if not isinstance(data, dict):
            return {"ok": False, "reason": "bad_json", "url": url}
        mode = str(data.get("mode") or "").strip().lower()
        if mode in _MOCK_MODES:
            return {
                "ok": False,
                "reason": "mock_sidecar",
                "mode": mode,
                "url": url,
            }
        if data.get("produces_output") is False:
            return {"ok": False, "reason": "no_output_capability", "url": url}
        if data.get("ok") is False:
            return {"ok": False, "reason": "health_not_ok", "url": url}
        return {
            "ok": True,
            "mode": mode or "production",
            "produces_output": data.get("produces_output", True),
            "service": data.get("service"),
            "url": url,
        }
    except Exception as exc:
        logger.debug("sidecar health probe failed %s: %s", url, exc)
        return {"ok": False, "reason": "unreachable", "error": str(exc), "url": url}


def is_verified_sidecar_url(base_url: str) -> bool:
    """实现 isverifiedsidecarURL 的功能。
    
    :param base_url: 参数 base_url（类型: str）
    :return: 返回 bool 结果
    """
    return bool(probe_sidecar_health(base_url).get("ok"))
