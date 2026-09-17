# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""发布分层路由 — 集 SAU / biliup / xhs-mcp / 原生 / AiToEarn。"""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.aitoearn_publish_adapter import aitoearn_enabled, preflight_aitoearn
from app.services.publish_workers.biliup_worker import biliup_enabled
from app.services.publish_workers.dual_line import dual_line_status
from app.services.publish_workers.sau_worker import SAU_SUPPORTED, sau_enabled
from app.services.publish_workers.xhs_mcp_worker import xhs_mcp_enabled

TIER_LABELS = {
    "native_youtube": "YouTube OAuth",
    "sau": "social-auto-upload",
    "biliup": "biliup",
    "xhs_mcp": "xiaohongshu-mcp",
    "aitoearn": "AiToEarn Relay",
}

_PLATFORM_TIERS: dict[str, tuple[str, ...]] = {
    "抖音": ("sau", "aitoearn"),
    "快手": ("sau", "aitoearn"),
    "哔哩哔哩": ("sau", "biliup", "aitoearn"),
    "小红书": ("xhs_mcp", "sau", "aitoearn"),
    "微信视频号": ("sau", "aitoearn"),
    "TikTok": ("sau", "aitoearn"),
    "TikTok / 抖音国际版": ("aitoearn",),
    "YouTube": ("aitoearn",),
    "Threads": ("aitoearn",),
    "LinkedIn": ("aitoearn",),
    "Facebook": ("aitoearn",),
    "Instagram": ("aitoearn",),
    "Twitter": ("aitoearn",),
    "X": ("aitoearn",),
    "Pinterest": ("aitoearn",),
    "Reddit": ("aitoearn",),
    "WhatsApp": ("aitoearn",),
}


def _tier_available(tier: str) -> bool:
    """实现 tieravailable 的功能。
    
    :param tier: 参数 tier（类型: str）
    :return: 返回 bool 结果
    """
    if tier == "sau":
        return sau_enabled()
    if tier == "biliup":
        return biliup_enabled()
    if tier == "xhs_mcp":
        return xhs_mcp_enabled()
    if tier == "aitoearn":
        return aitoearn_enabled()
    return False


def platform_tier_chain(platform_name: str) -> list[str]:
    """返回该平台当前环境可用的 Worker 优先级列表。"""
    raw = _PLATFORM_TIERS.get(platform_name, ("sau", "aitoearn"))
    return [t for t in raw if _tier_available(t)]


def any_publish_worker_ready() -> bool:
    """实现 any发布workerready 的功能。
    
    :return: 返回 bool 结果
    """
    return sau_enabled() or biliup_enabled() or xhs_mcp_enabled() or aitoearn_enabled()


def preflight_workers() -> dict[str, Any]:
    """Hermes / API 预检：各 Worker 就绪态（同步，不发起网络）。"""
    aito_ready = aitoearn_enabled()
    aito = {
        "ready": aito_ready,
        "reason": None if aito_ready else "未配置 AITOEARN_API_KEY",
        "account_count": 0,
        "accounts": [],
    }
    sau_ok = sau_enabled()
    from app.services.publish_workers.sau_sidecar import sau_sidecar_enabled, sau_sidecar_health
    sidecar = sau_sidecar_health() if sau_sidecar_enabled() else {"ok": False}
    dl = dual_line_status()
    return {
        "ready": dl.get("minimum_publish_ready"),
        "dual_line": dl,
        "workers": {
            "sau": {
                "enabled": sau_ok,
                "platforms": sorted(SAU_SUPPORTED) if sau_ok else [],
                "sidecar": sidecar if sau_sidecar_enabled() else None,
                "hint": None
                if sau_ok
                else "配置 SAU_SIDECAR_URL 或 SAU_CLI_PATH + playwright install",
            },
            "biliup": {
                "enabled": biliup_enabled(),
                "hint": None if biliup_enabled() else "安装 biliup CLI 并 biliup login",
            },
            "xhs_mcp": {
                "enabled": xhs_mcp_enabled(),
                "base_url": (settings.XHS_MCP_BASE_URL or "").strip() if xhs_mcp_enabled() else None,
                "hint": None if xhs_mcp_enabled() else "部署 xpzouying/xiaohongshu-mcp 并设 XHS_MCP_BASE_URL",
            },
            "aitoearn": aito,
        },
        "tier_labels": TIER_LABELS,
    }


async def preflight_workers_async() -> dict[str, Any]:
    """含 AiToEarn 连通性探测的完整预检。"""
    base = preflight_workers()
    if aitoearn_enabled():
        try:
            base["workers"]["aitoearn"] = await preflight_aitoearn()
        except Exception as exc:
            base["workers"]["aitoearn"] = {
                "ready": False,
                "reason": str(exc),
                "accounts": [],
            }
    base["ready"] = any(
        (base["workers"].get(k) or {}).get("enabled") or (base["workers"].get("aitoearn") or {}).get("ready")
        for k in ("sau", "biliup", "xhs_mcp")
    ) or bool((base["workers"].get("aitoearn") or {}).get("ready"))
    base["dual_line"] = dual_line_status()
    return base


def primary_worker_label(platform_name: str) -> str | None:
    """实现 primaryworkerlabel 的功能。
    
    :param platform_name: 参数 platform_name（类型: str）
    :return: 返回 str | None 结果
    """
    chain = platform_tier_chain(platform_name)
    if not chain:
        return None
    return TIER_LABELS.get(chain[0], chain[0])
