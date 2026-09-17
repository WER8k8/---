# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI Hunter 找客旁路 — 对接 xiongQvQ/AI_Find_Customer 式 Sidecar HTTP API。

主站不内置深度爬虫；Sidecar 返回须带 evidence_url，一律 human_verify。
兼容契约：
- POST /v1/find-prospects（优丁标准）
- POST /api/v1/hunts + 轮询（AI_Find_Customer 原生）
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 90.0
_HUNT_POLL_INTERVAL = 2.0
_HUNT_TERMINAL = frozenset({"completed", "failed", "cancelled"})


def sidecar_base_url() -> str:
    """sidecar_base_url。
    :return: 返回处理结果。
    """
    return (os.getenv("AI_FIND_CUSTOMER_URL") or "").strip().rstrip("/")


def sidecar_token() -> str:
    """sidecar_token。
    :return: 返回处理结果。
    """
    return (os.getenv("AI_FIND_CUSTOMER_TOKEN") or "").strip()


def allow_dev_stub() -> bool:
    """AI_FIND_CUSTOMER_ALLOW_DEV_STUB=0 时拒绝 mode=mock / probe_mode=stub。"""
    val = (os.getenv("AI_FIND_CUSTOMER_ALLOW_DEV_STUB") or "").strip().lower()
    if val in ("0", "false", "no", "off"):
        return False
    if os.getenv("ENVIRONMENT", "").strip().lower() == "production":
        return False
    return True


def _reject_if_stub_forbidden(packed: dict[str, Any] | None) -> dict[str, Any] | None:
    """_reject_if_stub_forbidden。

    参数说明：
    :param packed: 参数 packed
    :return: 返回处理结果。
    """
    if not packed:
        return None
    if allow_dev_stub():
        return packed
    mode = str(packed.get("mode") or "").lower()
    probe = str(packed.get("probe_mode") or "").strip()
    if probe == "stub" or mode == "mock":
        logger.warning(
            "ai_find_customer stub/mock rejected (AI_FIND_CUSTOMER_ALLOW_DEV_STUB=0)"
        )
        return None
    return packed


def ai_find_customer_sidecar_status() -> dict[str, Any]:
    """ai_find_customer_sidecar_status。
    :return: 返回处理结果。
    """
    base = sidecar_base_url()
    out: dict[str, Any] = {
        "configured": bool(base),
        "url": base or None,
        "healthy": None,
        "detail": None,
        "github_ref": "xiongQvQ/AI_Find_Customer",
        "contract_paths": ["/v1/find-prospects", "/api/v1/hunts"],
        "allow_dev_stub": allow_dev_stub(),
    }
    if not base:
        out["fallback"] = "accio_buyer_discovery_in_process"
        return out
    headers = _auth_headers()
    for path in ("/health", "/v1/health", "/api/health", "/api/v1/health"):
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
    out["fallback"] = "accio_buyer_discovery_in_process"
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


def _normalize_prospect(row: dict[str, Any]) -> dict[str, Any] | None:
    """_normalize_prospect。

    参数说明：
    :param row: 参数 row
    :return: 返回处理结果。
    """
    if not isinstance(row, dict):
        return None
    evidence = (
        row.get("evidence_url")
        or row.get("source_url")
        or row.get("url")
        or row.get("website")
        or ""
    )
    if isinstance(evidence, str):
        evidence = evidence.strip()
    else:
        evidence = str(evidence or "").strip()
    title = (
        row.get("title")
        or row.get("company")
        or row.get("company_name")
        or row.get("name")
        or ""
    ).strip()
    if not title and not evidence:
        return None
    confidence = row.get("confidence")
    try:
        conf_f = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        conf_f = None
    raw_score = row.get("fit_score")
    if raw_score is None:
        raw_score = row.get("score")
    try:
        fit_score = int(raw_score) if raw_score is not None else 60
    except (TypeError, ValueError):
        fit_score = 60
    if fit_score <= 1:
        fit_score = int(fit_score * 100)
    return {
        "title": title[:200] or "Prospect",
        "company": (row.get("company") or row.get("company_name") or title)[:200],
        "country_code": (row.get("country_code") or row.get("country") or "")[:8].upper(),
        "email": (row.get("email") or "")[:200] or None,
        "phone": (row.get("phone") or "")[:64] or None,
        "buyer_type": (row.get("buyer_type") or row.get("type") or "importer")[:32],
        "fit_score": min(95, max(40, fit_score)),
        "suggested_channel": (row.get("suggested_channel") or "email")[:32],
        "notes": (row.get("notes") or row.get("snippet") or "")[:2000],
        "evidence_url": evidence[:500] if evidence else None,
        "confidence": conf_f,
        "source_channel": (row.get("source") or row.get("source_channel") or "sidecar")[:32],
        "verification_status": "待核实候选",
    }


def _pack_prospects(
    prospects: list[dict[str, Any]],
    *,
    region: str,
    category: str,
    count: int,
    sidecar_path: str,
    probe_mode: str | None = None,
) -> dict[str, Any]:
    """_pack_prospects。

    参数说明：
    :param prospects: 参数 prospects
    :param region: 参数 region
    :param category: 参数 category
    :param count: 参数 count
    :param sidecar_path: 参数 sidecar_path
    :param probe_mode: 参数 probe_mode
    :return: 返回处理结果。
    """
    pack: dict[str, Any] = {
        "mode": "ai_find_customer_sidecar",
        "region": region,
        "category": category,
        "count": len(prospects),
        "prospects": prospects[:count],
        "human_verify_required": True,
        "disclaimer": (
            "Sidecar 找客结果须人工核实；每条线索须有可核对 evidence_url，"
            "禁止未核实直接群发。"
        ),
        "sidecar_path": sidecar_path,
    }
    if probe_mode:
        pack["probe_mode"] = probe_mode
        pack["disclaimer"] += " （当前为 development stub，非真实爬取结果。）"
    return pack


def _parse_prospect_payload(
    data: Any,
    *,
    region: str,
    category: str,
    count: int,
    sidecar_path: str,
) -> dict[str, Any] | None:
    """_parse_prospect_payload。

    参数说明：
    :param data: 参数 data
    :param region: 参数 region
    :param category: 参数 category
    :param count: 参数 count
    :param sidecar_path: 参数 sidecar_path
    :return: 返回处理结果。
    """
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    if not isinstance(data, dict):
        return None
    raw_items = (
        data.get("prospects")
        or data.get("leads")
        or data.get("items")
        or []
    )
    prospects: list[dict[str, Any]] = []
    for row in raw_items:
        norm = _normalize_prospect(row)
        if norm and norm.get("evidence_url"):
            prospects.append(norm)
    if not prospects:
        return None
    probe_mode = None
    if str(data.get("probe_mode") or "").strip():
        probe_mode = str(data.get("probe_mode")).strip()
    elif str(data.get("mode") or "").lower() == "mock":
        probe_mode = "stub"
    return _pack_prospects(
        prospects,
        region=region or str(data.get("region") or ""),
        category=category or str(data.get("category") or ""),
        count=count,
        sidecar_path=sidecar_path,
        probe_mode=probe_mode,
    )


def _fetch_via_find_prospects(
    *,
    base: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    region: str,
    category: str,
    count: int,
) -> dict[str, Any] | None:
    """_fetch_via_find_prospects。

    参数说明：
    :param base: 参数 base
    :param headers: 参数 headers
    :param payload: 参数 payload
    :param region: 参数 region
    :param category: 参数 category
    :param count: 参数 count
    :return: 返回处理结果。
    """
    for path in ("/v1/find-prospects", "/api/find-prospects", "/find-prospects"):
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.post(f"{base}{path}", json=payload, headers=headers)
            if resp.status_code >= 300:
                logger.info("ai_find_customer sidecar %s HTTP %s", path, resp.status_code)
                continue
            packed = _parse_prospect_payload(
                resp.json(),
                region=region,
                category=category,
                count=count,
                sidecar_path=path,
            )
            if packed:
                return packed
            logger.info(
                "ai_find_customer sidecar %s returned no evidence-backed prospects",
                path,
            )
        except Exception as exc:
            logger.info("ai_find_customer sidecar %s failed: %s", path, exc)
    return None


def _fetch_via_ai_hunter_hunts(
    *,
    base: str,
    headers: dict[str, str],
    query: str,
    region: str,
    category: str,
    count: int,
) -> dict[str, Any] | None:
    """AI_Find_Customer 原生：POST /api/v1/hunts → 轮询 status → result.leads。"""
    hunt_body: dict[str, Any] = {
        "description": query,
        "product_keywords": [w for w in (category or "").split() if w][:8],
        "target_customer_profile": category or "B2B distributor importer",
        "target_regions": [region] if region else [],
        "target_lead_count": max(3, min(int(count), 30)),
        "max_rounds": 3,
        "min_new_leads_threshold": min(3, count),
        "enable_email_craft": False,
    }
    hunt_paths = ("/api/v1/hunts", "/hunts")
    deadline = time.monotonic() + (_TIMEOUT - 5.0)
    for create_path in hunt_paths:
        hunt_id: str | None = None
        try:
            with httpx.Client(timeout=30.0) as client:
                create_resp = client.post(
                    f"{base}{create_path}",
                    json=hunt_body,
                    headers=headers,
                )
            if create_resp.status_code >= 300:
                logger.info(
                    "ai_find_customer hunt %s HTTP %s",
                    create_path,
                    create_resp.status_code,
                )
                continue
            created = create_resp.json()
            if isinstance(created, dict):
                hunt_id = str(created.get("hunt_id") or created.get("id") or "")
            if not hunt_id:
                continue

            status_prefix = create_path.rsplit("/hunts", 1)[0]
            status_base = f"{base}{status_prefix}/hunts/{hunt_id}"
            terminal_status = "pending"
            while time.monotonic() < deadline:
                with httpx.Client(timeout=15.0) as client:
                    status_resp = client.get(f"{status_base}/status", headers=headers)
                if status_resp.status_code >= 300:
                    break
                status_data = status_resp.json()
                terminal_status = str(
                    status_data.get("status") or status_data.get("state") or ""
                ).lower()
                if terminal_status in _HUNT_TERMINAL:
                    break
                time.sleep(_HUNT_POLL_INTERVAL)

            with httpx.Client(timeout=30.0) as client:
                result_resp = client.get(f"{status_base}/result", headers=headers)
            if result_resp.status_code >= 300:
                logger.info(
                    "ai_find_customer hunt result HTTP %s for %s",
                    result_resp.status_code,
                    hunt_id,
                )
                continue
            packed = _parse_prospect_payload(
                result_resp.json(),
                region=region,
                category=category,
                count=count,
                sidecar_path=f"{create_path}#{hunt_id}",
            )
            if packed:
                packed["hunt_id"] = hunt_id
                packed["hunt_status"] = terminal_status
                return packed
            logger.info(
                "ai_find_customer hunt %s finished without evidence-backed leads",
                hunt_id,
            )
        except Exception as exc:
            logger.info("ai_find_customer hunt via %s failed: %s", create_path, exc)
    return None


def fetch_sidecar_prospects(
    *,
    tenant_id: str,
    query: str,
    region: str = "",
    category: str = "",
    count: int = 8,
) -> dict[str, Any] | None:
    """调用找客 Sidecar；无配置或失败返回 None（由主站 Accio 模板兜底）。"""
    base = sidecar_base_url()
    if not base:
        return None
    payload = {
        "tenant_id": str(tenant_id),
        "query": query,
        "region": region,
        "category": category,
        "count": max(3, min(int(count), 30)),
    }
    headers = _auth_headers()
    packed = _fetch_via_find_prospects(
        base=base,
        headers=headers,
        payload=payload,
        region=region,
        category=category,
        count=count,
    )
    if packed:
        return _reject_if_stub_forbidden(packed)

    packed = _fetch_via_ai_hunter_hunts(
        base=base,
        headers=headers,
        query=query or f"{region} {category} B2B buyer",
        region=region,
        category=category,
        count=count,
    )
    return _reject_if_stub_forbidden(packed)
