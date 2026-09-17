# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""UserActionAnalyzePlatform Sidecar HTTP 客户端。"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.services.analytics.user_action_analytics_compliance import (
    assert_module_compliance,
    validate_analytics_result,
)
from app.services.analytics.user_action_analytics_registry import (
    module_by_id,
    registry_payload,
)

logger = logging.getLogger(__name__)

_TIMEOUT = 180.0


def sidecar_base_url() -> str:
    """实现 sidecarbaseURL 的功能。
    
    :return: 返回 str 结果
    """
    return (os.getenv("USER_ACTION_ANALYTICS_URL") or "").strip().rstrip("/")


def sidecar_token() -> str:
    """实现 sidecar令牌 的功能。
    
    :return: 返回 str 结果
    """
    return (os.getenv("USER_ACTION_ANALYTICS_TOKEN") or "").strip()


def user_action_analytics_sidecar_status() -> dict[str, Any]:
    """实现 用户actionanalyticssidecar状态 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    base = sidecar_base_url()
    out: dict[str, Any] = {
        "configured": bool(base),
        "url": base or None,
        "healthy": None,
        "github_ref": "oeljeklaus-you/UserActionAnalyzePlatform",
        "registry_count": len(registry_payload().get("items") or []),
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


def run_analytics_module(
    module_id: str,
    *,
    params: dict[str, Any] | None = None,
    tenant_id: str | None = None,
    operator_role: str | None = None,
    compliance_acknowledged: bool = False,
    tenant_consent: bool = False,
    purpose: str | None = None,
) -> dict[str, Any]:
    """实现 执行analyticsmodule 的功能。
    
    :param module_id: 参数 module_id（类型: str）
    :param params: 参数 params（类型: dict[str, Any] | None）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param operator_role: 参数 operator_role（类型: str | None）
    :param compliance_acknowledged: 参数 compliance_acknowledged（类型: bool）
    :param tenant_consent: 参数 tenant_consent（类型: bool）
    :param purpose: 参数 purpose（类型: str | None）
    :return: 返回 dict[str, Any] 结果
    """
    module = module_by_id(module_id)
    if not module:
        return {
            "ok": False,
            "error_code": "ANALYTICS_MODULE_UNKNOWN",
            "module_id": module_id,
        }

    decision = assert_module_compliance(
        module,
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
            "module_id": module_id,
            "note": decision.message,
        }

    base = sidecar_base_url()
    if not base:
        return {
            "ok": False,
            "error_code": "USER_ACTION_ANALYTICS_NOT_CONFIGURED",
            "module_id": module_id,
            "note": "请部署 Spark Sidecar 并配置 USER_ACTION_ANALYTICS_URL",
        }

    payload: dict[str, Any] = {
        "module_id": module_id,
        "upstream_module": module.upstream_module,
        "params": params or {},
        "purpose": purpose or (params or {}).get("purpose"),
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id

    paths = ("/v1/run-module", "/api/run-module", "/run-module")
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
            return validate_analytics_result(module, data, decision=decision)
        except Exception as exc:
            logger.warning("user action analytics sidecar %s failed: %s", path, exc)
    return {
        "ok": False,
        "error_code": "USER_ACTION_ANALYTICS_SIDECAR_ERROR",
        "module_id": module_id,
    }


def run_page_conversion_probe(
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    site: str | None = None,
) -> dict[str, Any]:
    """实现 执行pageconversion探测 的功能。
    
    :param start_date: 参数 start_date（类型: str | None）
    :param end_date: 参数 end_date（类型: str | None）
    :param site: 参数 site（类型: str | None）
    :return: 返回 dict[str, Any] 结果
    """
    params: dict[str, Any] = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if site:
        params["site"] = site
    return run_analytics_module(
        "page_conversion",
        params=params,
        purpose="独立站页面单跳转化分析",
        operator_role="system",
    )
