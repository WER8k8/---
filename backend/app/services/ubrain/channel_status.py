# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
FIX-5 / W4: Prospect channel availability service.

Centralizes API-availability checks for every prospect channel so that:
- Backend returns honest four-state status to the frontend / Hermes executor / bot
- Frontend can label unconfigured channels instead of faking them
- No more "fake channels that look real to users"

四态取值域（与前端 `frontend/admin/src/utils/channelStatus.ts` 对齐）：
  - "live":     已配置真实凭据，调用真实外部 API，产出可当真实商机
  - "mock":     走模拟数据 / 模板，非真实外部调用 —— 不可当真实商机
  - "degraded": 有实现但因缺 Key / 限流 / 降级回退而能力受损（需人工复核）
  - "blocked":  未配置 / 未接入 / 不可用，且无 mock 回退

判定原则（诚实优先）：
  * 一律基于「配置项是否真实存在」做判定，不做虚构的可用性宣称；
  * 空白字符串、None 一律视为未配置；
  * 为端点响应速度，本模块只读配置 / 环境变量，不发起网络探测；
  * 未配置但确有 mock 回退的渠道标 ``mock``；未配置且会诚实报错（无 mock）的标 ``blocked``。

向后兼容：``ChannelInfo.legacy_status`` 保留旧三态（real / mock / coming_soon）映射，
``ChannelInfo.is_mock`` 保留旧 ``status != "real"`` 语义，旧消费者可平滑迁移。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from app.core.config import settings


ChannelStatus = Literal["live", "mock", "degraded", "blocked"]

# 四态 → 旧三态（real / mock / coming_soon），供尚未迁移的消费者使用
_LEGACY_STATUS_MAP: dict[str, str] = {
    "live": "real",
    "mock": "mock",
    "degraded": "mock",
    "blocked": "coming_soon",
}


@dataclass(frozen=True)
class ChannelInfo:
    """Single prospect channel availability info."""
    id: str
    name: str
    status: ChannelStatus
    reason: str  # Human-readable explanation
    # 该渠道产出能否直接当作真实商机（mock/degraded/blocked 一律 False）
    trustworthy: bool = False

    @property
    def is_mock(self) -> bool:
        """旧语义兼容：非 live 即视为不可直接采信。"""
        return self.status != "live"

    @property
    def legacy_status(self) -> str:
        """旧三态取值（real / mock / coming_soon），兼容未迁移消费者。"""
        return _LEGACY_STATUS_MAP.get(self.status, "coming_soon")


def get_channel_status(channel_id: str) -> ChannelInfo:
    """Return the status of a single prospect channel."""
    checks = _all_channel_checks()
    return checks.get(channel_id, ChannelInfo(
        id=channel_id, name=channel_id,
        status="blocked",
        reason="未知渠道：未在任何适配器 / 配置中登记",
        trustworthy=False,
    ))


def get_all_channel_statuses() -> list[ChannelInfo]:
    """Return availability info for ALL prospect channels."""
    return list(_all_channel_checks().values())


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _flag(value: object) -> bool:
    """非空字符串视为已配置（None / "" / 纯空白 均为未配置）。"""
    return bool(str(value or "").strip())


# ---------------------------------------------------------------------------
# Internal: per-channel checks
# ---------------------------------------------------------------------------

def _all_channel_checks() -> dict[str, ChannelInfo]:
    """Evaluate each channel's readiness. Kept as a flat dict for O(1) lookup."""
    return {
        "google": _check_google(),
        "linkedin": _check_linkedin(),
        "tiktok": _check_tiktok(),
        "quora": _check_quora(),
        "reddit": _check_reddit(),
        "whatsapp": _check_whatsapp(),
        "email": _check_email(),
        "hunter": _check_hunter(),
        "apollo": _check_apollo(),
        "customs": _check_customs(),
        "b2b_platform": _check_b2b_platform(),
        "gsc_ads": _check_gsc_ads(),
        "tavily": _check_tavily(),
    }


def _check_google() -> ChannelInfo:
    """Google Custom Search（CSE）。未配置则返回演示数据。"""
    if _flag(settings.GOOGLE_CSE_API_KEY) and _flag(settings.GOOGLE_CSE_CX):
        return ChannelInfo(
            "google", "Google 搜索", "live",
            "GOOGLE_CSE_API_KEY / GOOGLE_CSE_CX 已配置，走真实 Custom Search API",
            True,
        )
    return ChannelInfo(
        "google", "Google 搜索", "mock",
        "未配置 GOOGLE_CSE_API_KEY / GOOGLE_CSE_CX，返回演示数据", False,
    )


def _check_linkedin() -> ChannelInfo:
    """LinkedIn。有 access_token 才算 live；仅 OAuth 凭证为 degraded。"""
    if _flag(settings.LINKEDIN_ACCESS_TOKEN):
        return ChannelInfo(
            "linkedin", "LinkedIn", "live",
            "LINKEDIN_ACCESS_TOKEN 已配置，走真实 API", True,
        )
    if _flag(settings.LINKEDIN_CLIENT_ID) and _flag(settings.LINKEDIN_CLIENT_SECRET):
        return ChannelInfo(
            "linkedin", "LinkedIn", "degraded",
            "OAuth 凭证已配置但未获取 access_token，能力受限（回退演示数据）", False,
        )
    return ChannelInfo(
        "linkedin", "LinkedIn", "mock",
        "未配置 LINKEDIN_CLIENT_ID / CLIENT_SECRET / ACCESS_TOKEN，返回演示数据", False,
    )


def _check_tiktok() -> ChannelInfo:
    """TikTok。渠道尚在开发，当前返回演示数据。"""
    return ChannelInfo(
        "tiktok", "TikTok", "mock",
        "TikTok 渠道尚在开发中，当前返回演示数据", False,
    )


def _check_quora() -> ChannelInfo:
    """Quora。渠道尚在开发，当前返回演示数据。"""
    return ChannelInfo(
        "quora", "Quora", "mock",
        "Quora 渠道尚在开发中，当前返回演示数据", False,
    )


def _check_reddit() -> ChannelInfo:
    """Reddit。渠道尚在开发，当前返回演示数据。"""
    return ChannelInfo(
        "reddit", "Reddit", "mock",
        "Reddit 渠道尚在开发中，当前返回演示数据", False,
    )


def _check_whatsapp() -> ChannelInfo:
    """WhatsApp Business Cloud API。未配置则返回演示数据。"""
    if _flag(settings.WHATSAPP_ACCESS_TOKEN) and _flag(settings.WHATSAPP_PHONE_NUMBER_ID):
        return ChannelInfo(
            "whatsapp", "WhatsApp", "live",
            "WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID 已配置", True,
        )
    return ChannelInfo(
        "whatsapp", "WhatsApp", "mock",
        "未配置 WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID，返回演示数据", False,
    )


def _check_email() -> ChannelInfo:
    """邮件触达（Resend / SMTP）。无 mock 回退，未配置即 blocked。"""
    configured = False
    provider = ""
    try:
        from app.services.ubrain.email_send_service import email_service_available
        configured = bool(email_service_available())
        if configured:
            provider = "Resend" if _flag(getattr(settings, "RESEND_API_KEY", "")) else "SMTP"
    except Exception:  # noqa: BLE001 — 降级为直接读配置
        if _flag(getattr(settings, "RESEND_API_KEY", "")):
            configured, provider = True, "Resend"
        elif _flag(getattr(settings, "SMTP_SERVER", "")):
            configured, provider = True, "SMTP"
    if configured:
        return ChannelInfo(
            "email", "邮件触达", "live",
            f"{provider or 'Resend/SMTP'} 已配置，走真实邮件发送与打开/点击追踪", True,
        )
    return ChannelInfo(
        "email", "邮件触达", "blocked",
        "未配置 RESEND_API_KEY / SMTP_SERVER，无法发信（诚实报错，无 mock 回退）", False,
    )


def _check_hunter() -> ChannelInfo:
    """Hunter.io 邮箱挖掘 / 验证。无 mock 回退，未配置即 blocked。"""
    has_key = _flag(os.getenv("HUNTER_API_KEY")) or _flag(os.getenv("HUNTER_IO_API_KEY"))
    if has_key:
        return ChannelInfo(
            "hunter", "Hunter.io", "live",
            "HUNTER_API_KEY 已配置，走真实邮箱挖掘 / 验证", True,
        )
    return ChannelInfo(
        "hunter", "Hunter.io", "blocked",
        "未配置 HUNTER_API_KEY，接口诚实报错（未配置即不可用，无 mock 回退）", False,
    )


def _check_apollo() -> ChannelInfo:
    """Apollo.io 人员 / 公司数据。无 mock 回退，未配置即 blocked。"""
    if _flag(os.getenv("APOLLO_API_KEY")):
        return ChannelInfo(
            "apollo", "Apollo.io", "live",
            "APOLLO_API_KEY 已配置，走真实人员 / 公司数据接口", True,
        )
    return ChannelInfo(
        "apollo", "Apollo.io", "blocked",
        "未配置 APOLLO_API_KEY，接口诚实报错（未配置即不可用，无 mock 回退）", False,
    )


def _check_customs() -> ChannelInfo:
    """海关 / 提单数据（CustomsDataSpider Sidecar）。产出为 research brief，须人工核实。"""
    if _flag(os.getenv("CUSTOMS_DATA_SPIDER_URL")):
        return ChannelInfo(
            "customs", "海关/提单数据", "live",
            "CUSTOMS_DATA_SPIDER_URL 已配置，Sidecar 可产出买家 research brief"
            "（须 evidence_url + 人工核实，不可直接当商机）", False,
        )
    return ChannelInfo(
        "customs", "海关/提单数据", "blocked",
        "未配置 CUSTOMS_DATA_SPIDER_URL，CustomsDataSpider Sidecar 未接入", False,
    )


def _check_b2b_platform() -> ChannelInfo:
    """B2B 平台询盘（Alibaba / Made-in-China / GlobalSources / IndiaMART）。

    收件箱中枢已实现字段清洗与归流，但未接入各平台官方 API，依赖人工 / 回传 payload。
    """
    return ChannelInfo(
        "b2b_platform", "B2B 平台询盘", "degraded",
        "B2B 平台收件箱中枢已实现（字段清洗 + 归流），但未接入平台官方 API，"
        "依赖人工 / 回传 payload，需人工复核", False,
    )


def _check_gsc_ads() -> ChannelInfo:
    """Google Search Console / Ads 归因 webhook。未配置密钥时端点返回 503。"""
    secret = _flag(getattr(settings, "GSC_ADS_WEBHOOK_SECRET", "")) or _flag(
        os.getenv("GSC_ADS_WEBHOOK_SECRET")
    )
    if secret:
        return ChannelInfo(
            "gsc_ads", "GSC/Ads 归因", "live",
            "GSC_ADS_WEBHOOK_SECRET 已配置，归因 webhook 接受真实信号", True,
        )
    return ChannelInfo(
        "gsc_ads", "GSC/Ads 归因", "blocked",
        "未配置 GSC_ADS_WEBHOOK_SECRET，归因 webhook 返回 503（dev 禁止伪造归因）", False,
    )


def _check_tavily() -> ChannelInfo:
    """Tavily 外网搜索（RADAR 雷达）。搜索结果非商机，需二次加工。"""
    configured = False
    try:
        from app.services.geo.tavily_search import tavily_configured
        configured = bool(tavily_configured())
    except Exception:  # noqa: BLE001 — 降级为直接读配置
        configured = _flag(getattr(settings, "TAVILY_API_KEY", ""))
    if configured:
        return ChannelInfo(
            "tavily", "Tavily 外网搜索", "live",
            "TAVILY_API_KEY 已配置，走真实外网搜索（结果为原始线索，需二次加工）", False,
        )
    return ChannelInfo(
        "tavily", "Tavily 外网搜索", "blocked",
        "未配置 TAVILY_API_KEY，外网搜索不可用", False,
    )
