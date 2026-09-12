"""发布能力注册表 — 多 Worker 真发，禁止假成功。"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.services.publish_workers.tier_router import (
    any_publish_worker_ready,
    platform_tier_chain,
    primary_worker_label,
)

logger = logging.getLogger(__name__)

# 两类"发不出去"的错误码 —— 编排层据此区分「渠道没配置」与「配置了但发失败」。
# PLATFORM_NOT_CONFIGURED：Publisher 已接入，但平台凭证（appid/token/cookies）缺失，未发起真实请求。
# PLATFORM_NOT_IMPLEMENTED：该平台压根没有真发实现（UnimplementedPublisher）。
# 两者都属"环境/接线未完成"，不等于业务失败；见 docs/编排主链打通实作记录-2026-09-10.md。
PLATFORM_NOT_CONFIGURED = "PLATFORM_NOT_CONFIGURED"
PLATFORM_NOT_IMPLEMENTED = "PLATFORM_NOT_IMPLEMENTED"

LIVE_PUBLISHER_KEYS = frozenset(
    {
        "facebook",
        "instagram",
        "twitter",
        "linkedin",
        "youtube",
        "wechat",
        "toutiao",
        "zhihu",
    }
)

TEXT_ADAPTER_PLATFORM_NAMES = frozenset(
    {
        "微信公众号",
        "百家号",
        "小红书",
        "知乎",
        "微博",
        "头条号",
        "CSDN",
    }
)

STUB_PUBLISHER_KEYS = frozenset(
    {
        "pinterest",
        "snapchat",
        "reddit",
        "tumblr",
        "threads",
        "pinterest",
        "weibo",
        "douyin",
        "kuaishou",
        "bilibili",
        "tmall",
        "taobao",
        "jd",
        "pinduoduo",
        "amazon",
        "ebay",
        "shopify",
        "woocommerce",
        "magento",
        "bigcommerce",
        "wix",
        "squarespace",
        "wordpress",
        "blogger",
        "medium",
        "substack",
        "telegram",
        "whatsapp_business",
        "discord",
        "slack",
        "google_business",
        "yelp",
        "tripadvisor",
        "wordpress_com",
        "linkedin_company",
        "tiktok",
    }
)

STUB_PLATFORM_DISPLAY_NAMES = frozenset(
    {
        "抖音",
        "快手",
        "哔哩哔哩",
        "微信视频号",
        "TikTok",
        "TikTok / 抖音国际版",
        "Threads",
        "Pinterest",
    }
)

VIDEO_MATRIX_PLATFORM_NAMES = STUB_PLATFORM_DISPLAY_NAMES | frozenset({"YouTube", "小红书"})


def has_video_payload(content: dict[str, Any]) -> bool:
    """has_video_payload。

    参数说明：
    :param content: 参数 content
    :return: 返回处理结果。
    """
    return bool((content.get("video_url") or "").strip())


def publish_block_reason(
    *,
    platform_name: str | None = None,
    publisher_key: str | None = None,
    content: dict[str, Any] | None = None,
) -> Optional[str]:
    """publish_block_reason。

    参数说明：
    :param platform_name: 参数 platform_name
    :param publisher_key: 参数 publisher_key
    :param content: 参数 content
    :return: 返回处理结果。
    """
    content = content or {}
    name = (platform_name or "").strip()
    key = (publisher_key or "").strip().lower()
    video = has_video_payload(content)
    if name in STUB_PLATFORM_DISPLAY_NAMES or key in STUB_PUBLISHER_KEYS:
        if video and name in VIDEO_MATRIX_PLATFORM_NAMES and platform_tier_chain(name):
            return None
        kind = "视频" if video else "内容"
        label = name or key or "该平台"
        return (
            f"{label} 无可用发布 Worker（请配置 SAU / biliup / xhs-mcp 或 AITOEARN_API_KEY）"
            if video
            else f"{label} 尚未接入真实{kind}发布 API"
        )

    if video and name in TEXT_ADAPTER_PLATFORM_NAMES and name != "小红书":
        return f"{name} 当前适配器仅支持图文，不支持 video_url 直发"

    if video and name == "小红书" and not platform_tier_chain(name):
        return "小红书 需部署 xiaohongshu-mcp 或 SAU / AiToEarn"

    if video and key and key not in LIVE_PUBLISHER_KEYS:
        if key not in {"youtube", "facebook", "instagram", "twitter", "linkedin"}:
            label = name or key
            if not platform_tier_chain(name):
                return f"{label} 视频发布 Worker 未配置"

    return None


_FAKE_POST_ID_PREFIXES = ("demo-", "fallback-", "yd_", "fake-", "stub-")
_FAKE_POST_IDS = frozenset({"pending", "pending_review", "unknown", "none", "null"})


def _is_plausible_platform_post_id(post_id: str) -> bool:
    """_is_plausible_platform_post_id。

    参数说明：
    :param post_id: 参数 post_id
    :return: 返回处理结果。
    """
    pid = post_id.strip()
    if not pid or len(pid) < 3:
        return False
    lower = pid.lower()
    if lower in _FAKE_POST_IDS:
        return False
    if any(lower.startswith(p) for p in _FAKE_POST_ID_PREFIXES):
        return False
    return True


def is_publish_result_success(result: dict[str, Any]) -> bool:
    """成功 = 有真实作品 URL，或可核对的平台原生 ID；否则一律失败。"""
    if result.get("verified") is False:
        return False
    url = (result.get("platform_post_url") or "").strip()
    if url.startswith("http"):
        if "/explore/pending" in url or url.rstrip("/").endswith("pending_review"):
            return False
        return True
    post_id = (result.get("platform_post_id") or "").strip()
    if _is_plausible_platform_post_id(post_id):
        return True
    return False


def normalize_publish_result(result: dict[str, Any]) -> dict[str, Any]:
    """统一收口：禁止 status=success 但无作品链接/ID 的假成功。"""
    out = dict(result)
    ok = is_publish_result_success(out)
    if ok:
        out["status"] = "success"
        out["success"] = True
        out["verified"] = True
        return out
    out["status"] = "failed"
    out["success"] = False
    out["verified"] = False
    if not (out.get("error_message") or "").strip():
        out["error_message"] = "发布未返回可验证作品链接（禁止假成功）"
    out["error_code"] = out.get("error_code") or "MISSING_POST_URL"
    return out


VIDEO_LIVE_PLATFORM_NAMES = frozenset({"YouTube"})


def video_publish_capability(
    *,
    platform_name: str | None = None,
    publisher_key: str | None = None,
) -> dict[str, Any]:
    """video_publish_capability。

    参数说明：
    :param platform_name: 参数 platform_name
    :param publisher_key: 参数 publisher_key
    :return: 返回处理结果。
    """
    name = (platform_name or "").strip()
    key = (publisher_key or "").strip().lower()
    probe = {"video_url": "https://probe.invalid/video.mp4"}
    blocked = publish_block_reason(
        platform_name=name,
        publisher_key=key,
        content=probe,
    )
    if blocked:
        return {
            "tier": "blocked",
            "selectable": False,
            "label": "未接入真发",
            "reason": blocked,
        }

    chain = platform_tier_chain(name)
    if chain:
        label = primary_worker_label(name) or chain[0]
        return {
            "tier": "live_video",
            "selectable": True,
            "label": f"真发 · {label}",
            "reason": f"Hermes 编排：{' → '.join(chain)}；成功须返回可验证作品链接",
            "worker_chain": chain,
        }

    if name in VIDEO_LIVE_PLATFORM_NAMES or key == "youtube":
        return {
            "tier": "live_video",
            "selectable": True,
            "label": "API 真发",
            "reason": "配置 OAuth 后上传；成功返回作品链接",
        }

    if key in {"facebook", "instagram", "twitter", "linkedin"}:
        return {
            "tier": "partial",
            "selectable": False,
            "label": "视频未验证",
            "reason": f"{name or key} 暂未开放 video_url 直发",
        }

    return {
        "tier": "unknown",
        "selectable": False,
        "label": "不可选",
        "reason": "视频直发 Worker 未配置",
    }


def publish_stack_summary() -> dict[str, Any]:
    """publish_stack_summary。
    :return: 返回处理结果。
    """
    from app.services.publish_workers.tier_router import preflight_workers
    return {
        "any_worker_ready": any_publish_worker_ready(),
        "preflight": preflight_workers(),
    }
