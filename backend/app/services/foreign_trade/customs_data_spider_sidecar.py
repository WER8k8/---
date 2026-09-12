"""CustomsDataSpider Sidecar — 海关买家 research brief，须 evidence_url + 人工核实。"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 90.0


def sidecar_base_url() -> str:
    """实现 sidecarbaseURL 的功能。
    
    :return: 返回 str 结果
    """
    return (os.getenv("CUSTOMS_DATA_SPIDER_URL") or "").strip().rstrip("/")


def sidecar_token() -> str:
    """实现 sidecar令牌 的功能。
    
    :return: 返回 str 结果
    """
    return (os.getenv("CUSTOMS_DATA_SPIDER_TOKEN") or "").strip()


def customs_data_spider_sidecar_status() -> dict[str, Any]:
    """实现 customs数据spidersidecar状态 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    base = sidecar_base_url()
    out: dict[str, Any] = {
        "configured": bool(base),
        "url": base or None,
        "healthy": None,
        "detail": None,
        "github_ref": "CustomsDataSpider",
        "contract_paths": ["/v1/buyer-research"],
        "compliance": "restricted",
    }
    if not base:
        out["fallback"] = "not_configured"
        return out
    headers = _auth_headers()
    for path in ("/health", "/v1/health"):
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


def _normalize_buyers(raw: list[Any], *, product: str, country_code: str | None) -> list[dict[str, Any]]:
    """实现 normalizebuyers 的功能。
    
    :param raw: 参数 raw（类型: list[Any]）
    :param product: 参数 product（类型: str）
    :param country_code: 参数 country_code（类型: str | None）
    :return: 返回 list[dict[str, Any]] 结果
    """
    valid: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        evidence = str(
            row.get("evidence_url") or row.get("source_url") or row.get("url") or ""
        ).strip()
        if not evidence:
            continue
        valid.append(
            {
                "company_name": str(row.get("company_name") or row.get("buyer") or row.get("name") or "")[
                    :200
                ],
                "country_code": str(
                    row.get("country_code") or country_code or ""
                ).upper()[:2]
                or None,
                "product_hint": str(row.get("product_hint") or product)[:200],
                "import_volume_hint": row.get("import_volume_hint"),
                "evidence_url": evidence[:500],
                "source_type": str(row.get("source_type") or "customs_sidecar")[:64],
            }
        )
    return valid


def fetch_customs_buyer_research(
    *,
    product: str,
    hs_code: str | None = None,
    country_code: str | None = None,
    tenant_id: str | None = None,
    max_results: int = 8,
) -> dict[str, Any] | None:
    """实现 获取customsbuyerresearch 的功能。
    
    :param product: 参数 product（类型: str）
    :param hs_code: 参数 hs_code（类型: str | None）
    :param country_code: 参数 country_code（类型: str | None）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param max_results: 参数 max_results（类型: int）
    :return: 返回 dict[str, Any] | None 结果
    """
    base = sidecar_base_url()
    if not base or not product.strip():
        return None
    payload = {
        "product": product.strip(),
        "hs_code": (hs_code or "").strip() or None,
        "country_code": (country_code or "").strip().upper()[:2] or None,
        "tenant_id": tenant_id,
        "max_results": max(1, min(int(max_results), 20)),
    }
    headers = _auth_headers()
    for path in ("/v1/buyer-research", "/api/buyer-research"):
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
            buyers = _normalize_buyers(
                data.get("buyers") or data.get("items") or [],
                product=product,
                country_code=country_code,
            )
            if not buyers:
                return None
            out: dict[str, Any] = {
                "buyers": buyers[:max_results],
                "buyer_count": len(buyers),
                "human_verify_required": True,
                "included": data.get("included"),
            }
            if str(data.get("mode") or "").lower() == "mock":
                out["probe_mode"] = "stub"
                out["included"] = None
            elif data.get("probe_mode"):
                out["probe_mode"] = data.get("probe_mode")
            if out.get("included") is True and not all(b.get("evidence_url") for b in buyers):
                out["included"] = None
            return out
        except Exception as exc:
            logger.info("customs sidecar %s failed: %s", path, exc)
    return None
