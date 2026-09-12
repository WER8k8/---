"""ECommerceCrawlers Sidecar — 外置 Python 爬虫 Worker HTTP 网关。"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.services.crawlers.ecommerce_crawlers_compliance import (
    assert_spider_compliance,
    validate_spider_result,
)
from app.services.crawlers.ecommerce_crawlers_registry import (
    recipe_by_id,
    registry_payload,
)

logger = logging.getLogger(__name__)

_TIMEOUT = 120.0


def sidecar_base_url() -> str:
    """实现 sidecarbaseURL 的功能。
    
    :return: 返回 str 结果
    """
    return (os.getenv("ECOMMERCE_CRAWLERS_URL") or "").strip().rstrip("/")


def sidecar_token() -> str:
    """实现 sidecar令牌 的功能。
    
    :return: 返回 str 结果
    """
    return (os.getenv("ECOMMERCE_CRAWLERS_TOKEN") or "").strip()


def ecommerce_crawlers_sidecar_status() -> dict[str, Any]:
    """实现 ecommercecrawlerssidecar状态 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    base = sidecar_base_url()
    out: dict[str, Any] = {
        "configured": bool(base),
        "url": base or None,
        "healthy": None,
        "github_ref": "DropsDevopsOrg/ECommerceCrawlers",
        "registry_count": len(registry_payload().get("items") or []),
        "callable_count": len(
            [i for i in (registry_payload().get("items") or []) if i.get("callable")]
        ),
        "social_spiders_enabled": (os.getenv("ECOMMERCE_SOCIAL_SPIDERS_ENABLED") or "")
        .strip()
        .lower()
        in ("1", "true", "yes"),
    }
    if not base:
        out["fallback"] = "not_configured"
        return out
    headers = _auth_headers()
    for path in ("/health", "/api/health", "/v1/health"):
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


def run_spider(
    spider_id: str,
    *,
    params: dict[str, Any] | None = None,
    tenant_id: str | None = None,
    operator_role: str | None = None,
    compliance_acknowledged: bool = False,
    tenant_consent: bool = False,
    purpose: str | None = None,
) -> dict[str, Any]:
    """调用 Sidecar 执行 spider；合规门禁 + evidence 校验。"""
    recipe = recipe_by_id(spider_id)
    if not recipe:
        return {
            "ok": False,
            "error_code": "SPIDER_UNKNOWN",
            "spider_id": spider_id,
        }

    decision = assert_spider_compliance(
        recipe,
        params=params,
        tenant_id=tenant_id,
        operator_role=operator_role,
        compliance_acknowledged=compliance_acknowledged,
        tenant_consent=tenant_consent,
        purpose=purpose,
    )
    if decision.verdict == "deny":
        return {
            "ok": False,
            "error_code": decision.error_code,
            "spider_id": spider_id,
            "note": decision.message,
        }

    if spider_id.startswith("media_"):
        from app.services.crawlers.media_crawler_sidecar import run_media_spider
        return run_media_spider(
            spider_id,
            params=params,
            tenant_id=tenant_id,
            purpose=purpose,
        )

    base = sidecar_base_url()
    if not base:
        return {
            "ok": False,
            "error_code": "ECOMMERCE_CRAWLERS_NOT_CONFIGURED",
            "spider_id": spider_id,
            "note": "请部署 Sidecar 并配置 ECOMMERCE_CRAWLERS_URL",
        }

    payload: dict[str, Any] = {
        "spider_id": spider_id,
        "repo_path": recipe.repo_path,
        "params": params or {},
        "compliance": recipe.compliance,
        "purpose": purpose or (params or {}).get("purpose"),
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id

    paths = ("/v1/run-spider", "/api/run-spider", "/run-spider")
    headers = _auth_headers()
    for path in paths:
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.post(f"{base}{path}", json=payload, headers=headers)
            if resp.status_code >= 300:
                continue
            raw = resp.json()
            data = raw.get("data") if isinstance(raw, dict) and "data" in raw else raw
            if not isinstance(data, dict):
                continue
            return validate_spider_result(recipe, data, decision=decision)
        except Exception as exc:
            logger.warning("ecommerce crawlers sidecar %s failed: %s", path, exc)
    return {
        "ok": False,
        "error_code": "ECOMMERCE_CRAWLERS_SIDECAR_ERROR",
        "spider_id": spider_id,
    }


def enrich_osint_with_qichacha(target: str, *, purpose: str | None = None) -> dict[str, Any] | None:
    """实现 enrichosintwithqichacha 的功能。
    
    :param target: 参数 target（类型: str）
    :param purpose: 参数 purpose（类型: str | None）
    :return: 返回 dict[str, Any] | None 结果
    """
    if not target or "@" in target:
        return None
    domain = target.replace("https://", "").replace("http://", "").split("/")[0]
    out = run_spider(
        "qichacha",
        params={"keyword": domain, "target": target},
        purpose=purpose or "osint_domain_enrichment",
        operator_role="system",
    )
    if out.get("ok") and (out.get("items") or out.get("evidence_url")):
        return out
    return None


def run_seo_baidu_probe(keyword: str, site: str | None = None) -> dict[str, Any]:
    """增长/SEO Lane：百度收录探针（Sidecar 可用时）。"""
    params: dict[str, Any] = {"keyword": keyword}
    if site:
        params["site"] = site
    return run_spider(
        "baidu_keyword",
        params=params,
        purpose="seo_inclusion_probe",
        operator_role="system",
    )
