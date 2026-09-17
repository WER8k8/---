# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
FIX-5: Prospect channel availability service.

Centralizes API-availability checks for all 6 prospect channels so that:
- Backend can return honest status to the frontend
- Frontend can hide/mock-indicate unconfigured channels via Feature Flag
- No more "fake channels that look real to users"

Each channel is either:
  - "real": API credentials are configured and the service calls real APIs
  - "mock": No credentials configured; returns hardcoded demo data
  - "coming_soon": Not yet implemented at all
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.config import settings


ChannelStatus = Literal["real", "mock", "coming_soon"]


@dataclass(frozen=True)
class ChannelInfo:
    """Single prospect channel availability info."""
    id: str
    name: str
    status: ChannelStatus
    reason: str  # Human-readable explanation


def get_channel_status(channel_id: str) -> ChannelInfo:
    """Return the status of a single prospect channel."""
    checks = _all_channel_checks()
    return checks.get(channel_id, ChannelInfo(
        id=channel_id, name=channel_id,
        status="coming_soon",
        reason="未知渠道",
    ))


def get_all_channel_statuses() -> list[ChannelInfo]:
    """Return availability info for ALL prospect channels."""
    return list(_all_channel_checks().values())


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
    }


def _check_google() -> ChannelInfo:
    """_check_google。
    :return: 返回处理结果。
    """
    if settings.GOOGLE_CSE_API_KEY and settings.GOOGLE_CSE_CX:
        return ChannelInfo("google", "Google 搜索", "real", "Google CSE API Key 和 CX 已配置")
    return ChannelInfo("google", "Google 搜索", "mock", "未配置 GOOGLE_CSE_API_KEY / GOOGLE_CSE_CX")


def _check_linkedin() -> ChannelInfo:
    """_check_linkedin。
    :return: 返回处理结果。
    """
    if settings.LINKEDIN_ACCESS_TOKEN:
        return ChannelInfo("linkedin", "LinkedIn", "real", "LinkedIn Sales Navigator API 已配置")
    if settings.LINKEDIN_CLIENT_ID and settings.LINKEDIN_CLIENT_SECRET:
        return ChannelInfo("linkedin", "LinkedIn", "mock", "LinkedIn OAuth 凭证已配置，但未获取 access_token，将使用演示数据")
    return ChannelInfo("linkedin", "LinkedIn", "mock", "未配置 LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET / LINKEDIN_ACCESS_TOKEN")


def _check_tiktok() -> ChannelInfo:
    """_check_tiktok。
    :return: 返回处理结果。
    """
    return ChannelInfo("tiktok", "TikTok", "mock", "TikTok 渠道尚在开发中，当前返回演示数据")


def _check_quora() -> ChannelInfo:
    """_check_quora。
    :return: 返回处理结果。
    """
    return ChannelInfo("quora", "Quora", "mock", "Quora 渠道尚在开发中，当前返回演示数据")


def _check_reddit() -> ChannelInfo:
    """_check_reddit。
    :return: 返回处理结果。
    """
    return ChannelInfo("reddit", "Reddit", "mock", "Reddit 渠道尚在开发中，当前返回演示数据")


def _check_whatsapp() -> ChannelInfo:
    """_check_whatsapp。
    :return: 返回处理结果。
    """
    if settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
        return ChannelInfo("whatsapp", "WhatsApp", "real", "WhatsApp Business API 凭证已配置")
    return ChannelInfo("whatsapp", "WhatsApp", "mock", "未配置 WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID")