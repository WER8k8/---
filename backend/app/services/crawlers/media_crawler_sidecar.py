"""MediaCrawler Sidecar — NanmiCoder/MediaCrawler HTTP gateway (social_restricted)."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 120.0


def sidecar_base_url() -> str:
    """实现 sidecarbaseURL 的功能。
    
    :return: 返回 str 结果
    """
    return (os.getenv("MEDIA_CRAWLER_URL") or "").strip().rstrip("/")


def sidecar_token() -> str:
    """实现 sidecar令牌 的功能。
    
    :return: 返回 str 结果
    """
    return (os.getenv("MEDIA_CRAWLER_TOKEN") or "").strip()


def media_crawler_sidecar_status() -> dict[str, Any]:
    """实现 mediacrawlersidecar状态 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    base = sidecar_base_url()
    out: dict[str, Any] = {
        "configured": bool(base),
        "url": base or None,
        "healthy": None,
        "detail": None,
        "github_ref": "NanmiCoder/MediaCrawler",
        "contract_paths": ["/v1/run-spider"],
        "social_spiders_enabled": (os.getenv("ECOMMERCE_SOCIAL_SPIDERS_ENABLED") or "")
        .strip()
        .lower()
        in ("1", "true", "yes"),
    }
    if not base:
        out["fallback"] = "not_configured"
        return out
    headers = _auth_headers()
    for path in ("/health", "/v1/health", "/api/health"):
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{base}{path}", headers=headers)
            if resp.status_code < 300:
                out["healthy"] = True
                out["health_path"] = path
                return out
            out["detail"] = f"{path}: HTTP {resp.status_code}"
        except Exception as exc:
            out["detail"] = str(exc)[:200]
    out["healthy"] = False
    return out


def _auth_headers() -> dict[str, str]:
    """实现 认证headers 的功能。
    
    :return: 返回 dict[str, str] 结果
    """
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = sidecar_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def run_media_spider(
    spider_id: str,
    *,
    params: dict[str, Any] | None = None,
    tenant_id: str | None = None,
    purpose: str | None = None,
) -> dict[str, Any]:
    """调用 MediaCrawler Sidecar；须已通过 ecommerce 合规门禁。"""
    base = sidecar_base_url()
    if not base:
        return {
            "ok": False,
            "error_code": "MEDIA_CRAWLER_NOT_CONFIGURED",
            "spider_id": spider_id,
            "note": "请部署 MediaCrawler Sidecar 并配置 MEDIA_CRAWLER_URL",
        }
    payload: dict[str, Any] = {
        "spider_id": spider_id,
        "params": params or {},
        "purpose": purpose or (params or {}).get("purpose"),
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id

    headers = _auth_headers()
    for path in ("/v1/run-spider", "/api/run-spider", "/run-spider"):
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.post(f"{base}{path}", json=payload, headers=headers)
            if resp.status_code >= 300:
                continue
            raw = resp.json()
            data = raw.get("data") if isinstance(raw, dict) and "data" in raw else raw
            if not isinstance(data, dict):
                continue
            items = data.get("items") or data.get("results") or []
            evidence = (data.get("evidence_url") or data.get("source_url") or "").strip()
            if not items and not evidence:
                return {
                    "ok": False,
                    "error_code": "MEDIA_CRAWLER_NO_EVIDENCE",
                    "spider_id": spider_id,
                }
            return {
                "ok": True,
                "spider_id": spider_id,
                "lane": "social_lead_intel",
                "compliance": "social_restricted",
                "human_review_required": True,
                "items": items if isinstance(items, list) else [],
                "evidence_url": evidence or None,
                "probe_mode": data.get("probe_mode"),
                "mode": data.get("mode"),
                "meta": {k: v for k, v in data.items() if k not in ("items", "results")},
            }
        except Exception as exc:
            logger.warning("media crawler sidecar %s failed: %s", path, exc)
    return {
        "ok": False,
        "error_code": "MEDIA_CRAWLER_SIDECAR_ERROR",
        "spider_id": spider_id,
    }
