# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""LibreTranslate 旁路 — 跨境文案机翻（须标注 machine_translated）。"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0


def sidecar_base_url() -> str:
    """实现 sidecarbaseURL 的功能。
    
    :return: 返回 str 结果
    """
    return (os.getenv("LIBRETRANSLATE_URL") or "").strip().rstrip("/")


def sidecar_token() -> str:
    """实现 sidecar令牌 的功能。
    
    :return: 返回 str 结果
    """
    return (os.getenv("LIBRETRANSLATE_TOKEN") or "").strip()


def libretranslate_sidecar_status() -> dict[str, Any]:
    """实现 libretranslatesidecar状态 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    base = sidecar_base_url()
    out: dict[str, Any] = {
        "configured": bool(base),
        "url": base or None,
        "healthy": None,
        "detail": None,
        "github_ref": "LibreTranslate/LibreTranslate",
        "contract_paths": ["/translate", "/languages"],
    }
    if not base:
        out["fallback"] = "not_configured"
        return out
    headers = _auth_headers()
    for path in ("/health", "/v1/health", "/languages"):
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


def translate_text(
    *,
    text: str,
    source: str = "zh",
    target: str = "en",
    tenant_id: str | None = None,
) -> dict[str, Any] | None:
    """实现 translate文本 的功能。
    
    :param text: 参数 text（类型: str）
    :param source: 参数 source（类型: str）
    :param target: 参数 target（类型: str）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :return: 返回 dict[str, Any] | None 结果
    """
    base = sidecar_base_url()
    if not base or not (text or "").strip():
        return None
    payload = {
        "q": text[:8000],
        "source": source,
        "target": target,
        "format": "text",
        "tenant_id": tenant_id,
    }
    headers = _auth_headers()
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(f"{base}/translate", json=payload, headers=headers)
        if resp.status_code >= 300:
            logger.warning("libretranslate HTTP %s", resp.status_code)
            return None
        body = resp.json()
        translated = (body.get("translatedText") or "").strip()
        if not translated:
            return None
        mode = body.get("mode") or ("mock" if body.get("probe_mode") == "stub" else "live")
        return {
            "translated_text": translated,
            "source": source,
            "target": target,
            "mode": mode,
            "machine_translated": True,
            "disclaimer": "机翻仅供参考，对外发送前须人工校对",
            "evidence_url": body.get("evidence_url"),
        }
    except Exception as exc:
        logger.warning("libretranslate failed: %s", exc)
        return None
