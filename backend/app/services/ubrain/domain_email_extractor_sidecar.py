"""官网域名邮箱 enrichment Sidecar — AI Hunter 后处理，须 source_url。"""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 45.0


def sidecar_base_url() -> str:
    """sidecar_base_url。
    :return: 返回处理结果。
    """
    return (os.getenv("DOMAIN_EMAIL_EXTRACTOR_URL") or "").strip().rstrip("/")


def sidecar_token() -> str:
    """sidecar_token。
    :return: 返回处理结果。
    """
    return (os.getenv("DOMAIN_EMAIL_EXTRACTOR_TOKEN") or "").strip()


def domain_email_extractor_sidecar_status() -> dict[str, Any]:
    """domain_email_extractor_sidecar_status。
    :return: 返回处理结果。
    """
    base = sidecar_base_url()
    out: dict[str, Any] = {
        "configured": bool(base),
        "url": base or None,
        "healthy": None,
        "detail": None,
        "github_ref": "EmailExtractor CLI class tools",
        "contract_paths": ["/v1/extract-emails"],
    }
    if not base:
        out["fallback"] = "skip_enrichment"
        return out
    headers = _auth_headers()
    for path in ("/health", "/v1/health", "/api/v1/health"):
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
    """_auth_headers。
    :return: 返回处理结果。
    """
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = sidecar_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def domain_from_url(url: str | None) -> str | None:
    """domain_from_url。

    参数说明：
    :param url: 参数 url
    :return: 返回处理结果。
    """
    raw = (url or "").strip()
    if not raw:
        return None
    if "@" in raw and not raw.startswith("http"):
        return None
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"
    try:
        host = urlparse(raw).netloc.lower()
    except Exception:
        return None
    if host.startswith("www."):
        host = host[4:]
    return host or None


def fetch_emails_for_domain(
    domain: str,
    *,
    tenant_id: str | None = None,
    max_emails: int = 5,
) -> dict[str, Any] | None:
    """调用 Sidecar 递归提取域名邮箱；失败返回 None。"""
    base = sidecar_base_url()
    dom = (domain or "").strip().lower()
    if not base or not dom:
        return None
    payload = {
        "domain": dom,
        "tenant_id": tenant_id,
        "max_emails": max(1, min(int(max_emails), 10)),
    }
    headers = _auth_headers()
    for path in ("/v1/extract-emails", "/api/extract-emails", "/extract-emails"):
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
            emails = data.get("emails") or []
            valid = []
            for row in emails:
                if not isinstance(row, dict):
                    continue
                email = str(row.get("email") or "").strip()
                source = str(row.get("source_url") or row.get("evidence_url") or "").strip()
                if email and source:
                    valid.append(
                        {
                            "email": email[:200],
                            "source_url": source[:500],
                            "role": row.get("role"),
                        }
                    )
            if not valid:
                return None
            out: dict[str, Any] = {
                "domain": dom,
                "emails": valid[: max_emails],
                "count": len(valid),
            }
            if data.get("probe_mode"):
                out["probe_mode"] = data.get("probe_mode")
            if str(data.get("mode") or "").lower() == "mock":
                out["probe_mode"] = out.get("probe_mode") or "stub"
            return out
        except Exception as exc:
            logger.info("domain_email_extractor %s failed: %s", path, exc)
    return None


def enrich_prospect_emails(
    prospects: list[dict[str, Any]],
    *,
    tenant_id: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """为缺 email 的潜客补 enrichment；不覆盖已有邮箱。"""
    if not sidecar_base_url() or not prospects:
        return prospects, None
    enriched = 0
    meta: dict[str, Any] = {"domains_queried": 0, "emails_added": 0}
    out_rows: list[dict[str, Any]] = []
    seen_domains: set[str] = set()
    cache: dict[str, dict[str, Any] | None] = {}
    for row in prospects:
        copy = dict(row)
        if copy.get("email"):
            out_rows.append(copy)
            continue
        dom = domain_from_url(copy.get("evidence_url") or copy.get("website"))
        if not dom or dom in seen_domains:
            if dom and dom in cache and cache[dom]:
                pack = cache[dom]
                if pack and pack.get("emails"):
                    first = pack["emails"][0]
                    copy["email"] = first["email"]
                    copy["email_source_url"] = first["source_url"]
                    copy["email_enrichment"] = "domain_sidecar"
                    enriched += 1
            out_rows.append(copy)
            continue
        seen_domains.add(dom)
        meta["domains_queried"] += 1
        pack = fetch_emails_for_domain(dom, tenant_id=tenant_id)
        cache[dom] = pack
        if pack and pack.get("probe_mode"):
            meta["probe_mode"] = pack.get("probe_mode")
        if pack and pack.get("emails"):
            first = pack["emails"][0]
            copy["email"] = first["email"]
            copy["email_source_url"] = first["source_url"]
            copy["email_enrichment"] = "domain_sidecar"
            enriched += 1
            meta["emails_added"] += 1
        out_rows.append(copy)

    if enriched == 0:
        return prospects, None
    meta["emails_added"] = enriched
    return out_rows, meta
