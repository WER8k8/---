# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
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
        # 海外 B2B 拓客（Alibaba 国际站 / Made-in-China / GlobalSources）
        "alibaba",
        "made_in_china",
        "globalsources",
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
        # --- 09-13 全平台对齐补齐（PC-05）：与 publish_service.PUBLISHER_MAP 里的
        # UnimplementedPublisher 键一一对应。登记在此，rank registry 的 adapter 口径
        # 与 publish_block_reason 才能认出它们是「已登记、未接真发」，
        # 而不是当成未知键放行 —— 未知键 + 视频内容会一路落到默认 Worker 链上假可选。
        "wechat_channels",
        "qieehao",
        "wangyi_hao",
        "sohu_hao",
        "yidianzixun",
        "dayuhao",
        "jianshu",
        "maimai",
        "taobao_guangguang",
        "ali1688",
        "huizhong",
        "line_official",
        "zalo",
        "vk",
        "quora",
        "amazon_seller",
        "tradekey",
        "kompass",
        "thomasnet",
        "aliexpress",
        "shopee",
        "lazada",
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
        # 文案保留机器可读码：下游 classify_publish_failure 的排除判定依赖它，
        # 缺配置 = NOT_CONFIGURED，未实现 = NOT_IMPLEMENTED，二者都不能误判成 cookie 过期
        return (
            f"{label} 无可用发布 Worker（请配置 SAU / biliup / xhs-mcp 或 AITOEARN_API_KEY）"
            f"（PLATFORM_NOT_CONFIGURED）"
            if video
            else f"{label} 尚未接入真实{kind}发布 API（PLATFORM_NOT_IMPLEMENTED）"
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


# ── M3 · per-platform 八标志位能力契约（模块5 契约 §5.1 / §5.2，G4 机器可读真值）────
# 八步与设计稿 §5.7「每个平台完成 8 步才能计入真实 40+」一一对应：
#   Adapter → Credential → Preflight → Dry Run → Real Publish → Status Poll
#   → Failure Mapping → Idempotency
ADMISSION_STEPS = ("adapter", "credential", "preflight", "dry_run",
                  "real_publish", "status_poll", "failure_mapping", "idempotency")


def _empty_flags() -> dict[str, bool]:
    """全 False 八标志位基线（桩平台 / 未登记平台现值）。"""
    return {s: False for s in ADMISSION_STEPS}


def _flags(**kw: bool) -> dict[str, bool]:
    base = _empty_flags()
    for k, v in kw.items():
        base[k] = bool(v)
    return base


# 每平台八标志位现值（§5.2 逐格标注）。
# 唯一硬闸：Dry Run 全 False + 凭据全空 → 现 0 平台计入「真实 40+」。
# 随 M1-M5 落地 / 真发证据核验后，经 register_platform_admission 逐格翻真。
PLATFORM_ADMISSION: dict[str, dict[str, bool]] = {
    # 真发·海外 API（§5.2 第 2 行：adapter ✅ / credential ❌ / preflight 🟠→真 / dry_run ❌ /
    # real_publish ✅ 类在 / status_poll 仅 AiToEarn → youtube 真 / failure_mapping 🟠→False /
    # idempotency 🟠→False）
    "facebook":      _flags(adapter=True, preflight=True, real_publish=True),
    "instagram":     _flags(adapter=True, preflight=True, real_publish=True),
    "twitter":       _flags(adapter=True, preflight=True, real_publish=True),
    "linkedin":      _flags(adapter=True, preflight=True, real_publish=True),
    "youtube":       _flags(adapter=True, preflight=True, real_publish=True, status_poll=True),
    # 真发·图文 C 端 Cookie（§5.2 第 1 行）
    "wechat":        _flags(adapter=True, preflight=True, real_publish=True),
    "toutiao":       _flags(adapter=True, preflight=True, real_publish=True),
    "zhihu":         _flags(adapter=True, preflight=True, real_publish=True),
    # B2B 适配（§5.2 第 3 行）
    "alibaba":         _flags(adapter=True, real_publish=True),
    "made_in_china":   _flags(adapter=True, real_publish=True),
    "globalsources":   _flags(adapter=True, real_publish=True),
}


def _ensure_all_publisher_keys_registered() -> None:
    """把 PUBLISHER_MAP 全部键补登记进八标志位（缺省全 False，桩 56 键防漏）。"""
    from app.services.publish_service import PUBLISHER_MAP

    for k in PUBLISHER_MAP:
        PLATFORM_ADMISSION.setdefault(k, _empty_flags())


_ensure_all_publisher_keys_registered()


def platform_admission_flags(platform_key: str) -> dict[str, bool]:
    """取某平台八标志位现值（未登记 → 全 False；绝不抛错）。"""
    key = (platform_key or "").strip().lower()
    reg = PLATFORM_ADMISSION.get(key)
    if reg is None:
        return _empty_flags()
    return {s: bool(reg.get(s, False)) for s in ADMISSION_STEPS}


def platform_admitted(platform_key: str) -> bool:
    """「计入真实 40+」判定 = 八标志位全 True（契约 §5.1）。

    现值：0 平台（§5.2 结论）；随 M1-M5 逐格翻真后自动放行。
    """
    m = platform_admission_flags(platform_key)
    return all(m.get(s) is True for s in ADMISSION_STEPS)


def admitted_platform_count() -> int:
    """当前计入「真实 40+」的平台数（G4 机器可读真值，现值 0）。"""
    return sum(1 for k in PLATFORM_ADMISSION if platform_admitted(k))


def register_platform_admission(platform_key: str, **flags: bool) -> dict[str, bool]:
    """把某平台八标志位**部分**翻真（真发证据核验后调用，M1-M5 落地）。

    - 只允许往 True 写；传 False 被忽略（防误把已验证项翻回 False）。
    - 平台键必须是 PUBLISHER_MAP 已登记键，否则 ValueError（拒绝凭空造平台）。
    - 八步之外不接受新维度（未知键 ValueError）。
    """
    key = (platform_key or "").strip().lower()
    from app.services.publish_service import PUBLISHER_MAP

    if key not in PUBLISHER_MAP:
        raise ValueError(f"平台未登记 PUBLISHER_MAP: {platform_key!r}")
    bad = [f for f in flags if f not in ADMISSION_STEPS]
    if bad:
        raise ValueError(f"未知八标志位维度: {bad}")
    m = PLATFORM_ADMISSION.setdefault(key, _empty_flags())
    for f in flags:
        if flags[f] is True:
            m[f] = True
    return platform_admission_flags(key)


def dry_run_publish(db: Any, *, tenant_id: str, platform_id: str,
                    content: dict) -> dict[str, Any]:
    """M3 §5.3：只做校验与 payload 构建，**不发起任何网络请求**。

    执行链：resolve_publish_credential（§4 唯一出口，fail-closed）
    → publish_block_reason（:146）→ 构建 payload。
    返回 {"ok", "credential_source", "blocked_reason", "would_target", "error_code"}。
    用途：把八标志位中的 dry_run 翻真；建任务前的可选前置校验。
    """
    from app.models.content import Platform
    from app.services.publish_service import PublishService

    out: dict[str, Any] = {
        "ok": False, "credential_source": "none",
        "blocked_reason": None, "would_target": {}, "error_code": None,
    }
    if db is None:
        out["blocked_reason"] = "缺少数据库会话"
        out["error_code"] = "no_session"
        return out

    # ① 平台目录命中（按 id 或 name 精确命中；platforms 表无 publisher_key 列，
    #    键解析走 PublishService.find_platform_config 的目录口径）
    cfg = db.query(Platform).filter(
        (Platform.id == str(platform_id)) | (Platform.name == str(platform_id))
    ).first()
    if cfg is None:
        out["blocked_reason"] = f"平台不在目录: {platform_id}"
        out["error_code"] = PLATFORM_NOT_CONFIGURED
        return out

    key = str(cfg.id or platform_id).strip().lower()
    name = str(cfg.name or "")

    # ② 凭据（fail-closed：缺凭据不发网络）
    cred = PublishService(db).resolve_publish_credential(str(tenant_id), str(cfg.id), None)
    out["credential_source"] = str(cred.get("source") or "none")
    if cred.get("error_code") == "credential_missing" or not cred.get("values"):
        out["blocked_reason"] = "credential_missing（租户未配置该平台凭据，fail-closed 不发网络）"
        out["error_code"] = "credential_missing"
        return out

    # ③ 平台级阻断（未接真发 / 图文不支持视频等，registry:146）
    blocked = publish_block_reason(
        platform_name=name,
        publisher_key=key,
        content=content or {},
    )
    if blocked:
        out["blocked_reason"] = blocked
        out["error_code"] = (
            PLATFORM_NOT_IMPLEMENTED
            if "PLATFORM_NOT_IMPLEMENTED" in blocked
            else PLATFORM_NOT_CONFIGURED
        )
        return out

    # ④ 构建 payload（只构建，不发网络）
    out["would_target"] = {
        "platform_id": str(cfg.id),
        "publisher_key": key,
        "content": dict(content or {}),
    }
    out["ok"] = True
    return out


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

    # 未接入真发 Worker 的平台一律不可选，禁止「查无此文」假发布
    if name in VIDEO_LIVE_PLATFORM_NAMES or key == "youtube":
        if not any_publish_worker_ready():
            return {
                "tier": "blocked",
                "selectable": False,
                "label": "未接入真发",
                "reason": "YouTube 直发 Worker 未就绪，不可选",
            }
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
