"""LinkedIn 决策人 enrichment Sidecar — P3 restricted，须 evidence_url + 人工核实。"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 60.0


def sidecar_base_url() -> str:
    """sidecar_base_url。
    :return: 返回处理结果。
    """
    return (os.getenv("LINKEDIN_DECISION_MAKER_URL") or "").strip().rstrip("/")


def sidecar_token() -> str:
    """sidecar_token。
    :return: 返回处理结果。
    """
    return (os.getenv("LINKEDIN_DECISION_MAKER_TOKEN") or "").strip()


def linkedin_decision_maker_sidecar_status() -> dict[str, Any]:
    """linkedin_decision_maker_sidecar_status。
    :return: 返回处理结果。
    """
    base = sidecar_base_url()
    out: dict[str, Any] = {
        "configured": bool(base),
        "url": base or None,
        "healthy": None,
        "detail": None,
        "github_ref": "tufayellus/linkedin-scraper",
        "contract_paths": ["/v1/decision-makers"],
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
    """_auth_headers。
    :return: 返回处理结果。
    """
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = sidecar_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_decision_makers(
    *,
    company: str,
    domain: str = "",
    industry: str = "",
    tenant_id: str | None = None,
    max_results: int = 5,
) -> dict[str, Any] | None:
    """fetch_decision_makers。

    参数说明：
    :param company: 参数 company
    :param domain: 参数 domain
    :param industry: 参数 industry
    :param tenant_id: 参数 tenant_id
    :param max_results: 参数 max_results
    :return: 返回处理结果。
    """
    base = sidecar_base_url()
    if not base or not (company or domain).strip():
        return None
    payload = {
        "company": company.strip(),
        "domain": domain.strip(),
        "industry": industry.strip(),
        "tenant_id": tenant_id,
        "max_results": max(1, min(int(max_results), 10)),
    }
    headers = _auth_headers()
    for path in ("/v1/decision-makers", "/api/decision-makers"):
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
            contacts = data.get("contacts") or data.get("items") or []
            valid = []
            for row in contacts:
                if not isinstance(row, dict):
                    continue
                evidence = str(
                    row.get("evidence_url") or row.get("linkedin_url") or row.get("url") or ""
                ).strip()
                if not evidence:
                    continue
                valid.append(
                    {
                        "name": str(row.get("name") or row.get("title") or "Contact")[:120],
                        "title": str(row.get("title") or row.get("role") or "")[:120],
                        "company": str(row.get("company") or company)[:200],
                        "linkedin_url": evidence[:500],
                        "evidence_url": evidence[:500],
                        "email": row.get("email"),
                        "country_code": row.get("country_code"),
                    }
                )
            if not valid:
                return None
            out: dict[str, Any] = {
                "contacts": valid[:max_results],
                "count": len(valid),
                "human_verify_required": True,
            }
            if data.get("probe_mode"):
                out["probe_mode"] = data.get("probe_mode")
            if str(data.get("mode") or "").lower() == "mock":
                out["probe_mode"] = out.get("probe_mode") or "stub"
            return out
        except Exception as exc:
            logger.info("linkedin sidecar %s failed: %s", path, exc)
    return None
