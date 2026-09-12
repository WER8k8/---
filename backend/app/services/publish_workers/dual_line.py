"""双线发布 — 主路（SAU/专用 Worker）+ 备路（AiToEarn）同时部署，主败备上。"""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.aitoearn_publish_adapter import aitoearn_enabled
from app.services.publish_workers.biliup_worker import biliup_enabled
from app.services.publish_workers.sau_worker import sau_enabled
from app.services.publish_workers.xhs_mcp_worker import xhs_mcp_enabled

DOMESTIC_VIDEO_PLATFORMS = frozenset(
    {
        "抖音",
        "快手",
        "哔哩哔哩",
        "小红书",
        "微信视频号",
    }
)


def primary_line_ready() -> bool:
    """实现 primarylineready 的功能。
    
    :return: 返回 bool 结果
    """
    return sau_enabled() or biliup_enabled() or xhs_mcp_enabled()


def fallback_line_ready() -> bool:
    """实现 fallbacklineready 的功能。
    
    :return: 返回 bool 结果
    """
    return aitoearn_enabled()


def dual_line_status() -> dict[str, Any]:
    """
    双线就绪态（部署并行，运行串行 failover，避免同一视频发两次）。
    - primary: 自托管 SAU / biliup / xhs-mcp
    - fallback: AiToEarn Relay
    """
    primary = primary_line_ready()
    fallback = fallback_line_ready()
    dual = primary and fallback
    minimum = primary or fallback
    warnings: list[str] = []
    if not primary:
        warnings.append("主路未就绪：请安装 SAU 并完成各平台 login")
    if not fallback:
        warnings.append("备路未就绪：请配置 AITOEARN_API_KEY 并在 aitoearn.cn 绑号")
    if primary and not fallback:
        warnings.append("仅主路可用：主路失败时无法自动切换备路，客户体验风险高")
    if fallback and not primary:
        warnings.append("仅备路可用：依赖第三方 Relay，建议并行部署 SAU 主路")

    return {
        "strategy": "primary_then_fallback",
        "description": "主路失败自动切备路；两条线同时配置，单次发布只走一条，避免重复发稿",
        "primary_line_ready": primary,
        "fallback_line_ready": fallback,
        "dual_line_ready": dual,
        "minimum_publish_ready": minimum,
        "customer_safe_recommended": dual,
        "require_dual_line": bool(settings.PUBLISH_DUAL_LINE_REQUIRED),
        "warnings": warnings,
        "primary_workers": {
            "sau": sau_enabled(),
            "biliup": biliup_enabled(),
            "xhs_mcp": xhs_mcp_enabled(),
        },
    }


def dual_line_block_reason(*, platform_names: list[str] | None = None) -> str | None:
    """生产门禁：外站国内平台发布要求双线就绪。"""
    if not settings.PUBLISH_DUAL_LINE_REQUIRED:
        return None
    names = set(platform_names or [])
    if not names.intersection(DOMESTIC_VIDEO_PLATFORMS):
        return None
    st = dual_line_status()
    if st.get("dual_line_ready"):
        return None
    if not st.get("minimum_publish_ready"):
        return "视频外站发布未就绪：请同时配置 SAU 主路与 AiToEarn 备路后再对客户开放"
    return (
        "双线冗余未满足（生产要求 SAU + AiToEarn 同时就绪）："
        + "；".join(st.get("warnings") or [])
    )


def annotate_failover_result(
    outcome: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    """标记本次成功走主路还是备路 failover。"""
    if not outcome.get("success"):
        outcome["publish_line"] = "none"
        outcome["failover"] = False
        if len(attempts) >= 2:
            outcome["failover_attempted"] = True
            outcome["primary_errors"] = [
                a.get("error_message") for a in attempts[:-1] if a.get("error_message")
            ]
        return outcome

    winning = attempts[-1] if attempts else {}
    tier = winning.get("tier") or outcome.get("tier") or outcome.get("via")
    is_fallback = tier == "aitoearn" and len(attempts) > 1
    outcome["publish_line"] = "fallback" if is_fallback else "primary"
    outcome["failover"] = is_fallback
    if is_fallback and attempts:
        outcome["primary_line_error"] = attempts[0].get("error_message")
    return outcome
