# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""出海参谋 M2 — 商业海关 API 适配层（可配置外部数据源）。"""

from __future__ import annotations

import os
from typing import Any

import httpx

from app.services.trade_intel_customs_service import customs_stats_for_category

DEFAULT_TIMEOUT = 8.0


def commercial_customs_stats(category: str) -> dict[str, Any]:
    """
    优先调用 TRADE_INTEL_M2_API_URL；未配置或失败时回退 M1 公开统计试点。
    期望外部 API JSON: { "rows": [...], "source": "...", "source_url": "..." }
    """
    base = (os.getenv("TRADE_INTEL_M2_API_URL") or "").strip().rstrip("/")
    if not base:
        data = customs_stats_for_category(category)
        data["rows"] = data.get("items") or []
        data["mode"] = "m1_fallback"
        data["m2_configured"] = False
        return data

    url = f"{base}/customs-stats"
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.get(url, params={"category": category})
            resp.raise_for_status()
            payload = resp.json()
            rows = payload.get("rows") or payload.get("data") or []
            return {
                "category": category,
                "mode": "m2_commercial",
                "m2_configured": True,
                "rows": rows,
                "source": payload.get("source") or "commercial_api",
                "source_url": payload.get("source_url"),
                "disclaimer": payload.get(
                    "disclaimer",
                    "商业数据仅供参考，签约前请核实来源与有效期。",
                ),
            }
    except Exception as exc:
        data = customs_stats_for_category(category)
        data["rows"] = data.get("items") or []
        data["mode"] = "m1_fallback_after_m2_error"
        data["m2_configured"] = True
        data["m2_error"] = str(exc)[:200]
        return data
