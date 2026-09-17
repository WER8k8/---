# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""IM 渠道多语言文案与访客解析（12 语种）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.im_routing_and_specs import MerchantIMRouting

# ISO 639-1，覆盖建材外贸常见市场（Tier1 核心 12 语 + Tier2 扩展 12 语 = 24 语）
SUPPORTED_LANGUAGES: dict[str, str] = {
    "zh": "中文",
    "en": "English",
    "ar": "العربية",
    "es": "Español",
    "pt": "Português",
    "ru": "Русский",
    "th": "ไทย",
    "vi": "Tiếng Việt",
    "id": "Bahasa Indonesia",
    "ms": "Bahasa Melayu",
    "ja": "日本語",
    "ko": "한국어",
    # Tier2 扩展语种（AI 翻译驱动，模板回退仅覆盖主力语种）
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "nl": "Nederlands",
    "pl": "Polski",
    "tr": "Türkçe",
    "hi": "हिन्दी",
    "bn": "বাংলা",
    "fa": "فارسی",
    "he": "עברית",
    "uk": "Українська",
    "fil": "Filipino",
}

CHANNEL_LABELS: dict[str, dict[str, str]] = {
    "whatsapp": {
        "zh": "WhatsApp 咨询",
        "en": "Chat on WhatsApp",
        "ar": "تواصل عبر واتساب",
        "es": "Chatear por WhatsApp",
        "pt": "Conversar no WhatsApp",
        "ru": "Написать в WhatsApp",
        "th": "แชทผ่าน WhatsApp",
        "vi": "Nhắn qua WhatsApp",
        "id": "Chat di WhatsApp",
        "ms": "Sembang WhatsApp",
        "ja": "WhatsAppで相談",
        "ko": "WhatsApp 상담",
    },
    "telegram": {
        "zh": "Telegram 咨询",
        "en": "Chat on Telegram",
        "ar": "تواصل عبر تيليجرام",
        "es": "Chatear por Telegram",
        "pt": "Conversar no Telegram",
        "ru": "Написать в Telegram",
        "th": "แชทผ่าน Telegram",
        "vi": "Nhắn qua Telegram",
        "id": "Chat di Telegram",
        "ms": "Sembang Telegram",
        "ja": "Telegramで相談",
        "ko": "Telegram 상담",
    },
    "line": {
        "zh": "LINE 咨询",
        "en": "Chat on LINE",
        "es": "Chatear por LINE",
        "pt": "Conversar no LINE",
        "th": "แชทผ่าน LINE",
        "ja": "LINEで相談",
        "ko": "LINE 상담",
    },
    "zalo": {
        "zh": "Zalo 咨询",
        "en": "Chat on Zalo",
        "vi": "Nhắn qua Zalo",
    },
    "live_chat": {
        "zh": "在线客服",
        "en": "Live Chat",
        "ar": "دردشة مباشرة",
        "es": "Chat en vivo",
        "pt": "Chat ao vivo",
        "ru": "Онлайн-чат",
        "th": "แชทสด",
        "vi": "Trò chuyện trực tuyến",
        "id": "Obrolan langsung",
        "ms": "Sembang langsung",
        "ja": "ライブチャット",
        "ko": "실시간 상담",
    },
    "form": {
        "zh": "提交询盘",
        "en": "Send Inquiry",
        "ar": "إرسال استفسار",
        "es": "Enviar consulta",
        "pt": "Enviar consulta",
        "ru": "Отправить запрос",
        "th": "ส่งคำถาม",
        "vi": "Gửi yêu cầu",
        "id": "Kirim pertanyaan",
        "ms": "Hantar pertanyaan",
        "ja": "お問い合わせ",
        "ko": "문의하기",
    },
}

COUNTRY_DEFAULT_LANG: dict[str, str] = {
    "CN": "zh",
    "TW": "zh",
    "HK": "zh",
    "US": "en",
    "GB": "en",
    "AU": "en",
    "SA": "ar",
    "AE": "ar",
    "ES": "es",
    "MX": "es",
    "BR": "pt",
    "RU": "ru",
    "TH": "th",
    "VN": "vi",
    "ID": "id",
    "MY": "ms",
    "JP": "ja",
    "KR": "ko",
}


def normalize_language(language: str | None, country_code: str | None) -> str:
    """normalize_language。

    参数说明：
    :param language: 参数 language
    :param country_code: 参数 country_code
    :return: 返回处理结果。
    """
    code = (language or "").strip().lower()[:2]
    if code in SUPPORTED_LANGUAGES:
        return code
    cc = (country_code or "").strip().upper()
    return COUNTRY_DEFAULT_LANG.get(cc, "en")


def localized_channel_label(channel_type: str, language: str) -> str:
    """localized_channel_label。

    参数说明：
    :param channel_type: 参数 channel_type
    :param language: 参数 language
    :return: 返回处理结果。
    """
    lang = normalize_language(language, None)
    by_channel = CHANNEL_LABELS.get(channel_type, {})
    return by_channel.get(lang) or by_channel.get("en") or "Contact Us"


def generate_im_link(channel_type: str, account_id: str) -> str:
    """generate_im_link。

    参数说明：
    :param channel_type: 参数 channel_type
    :param account_id: 参数 account_id
    :return: 返回处理结果。
    """
    if channel_type == "whatsapp":
        return f"https://wa.me/{account_id}"
    if channel_type == "telegram":
        return f"https://t.me/{account_id}"
    if channel_type == "line":
        return f"https://line.me/ti/p/{account_id}"
    if channel_type == "zalo":
        return f"https://zalo.me/{account_id}"
    if channel_type == "form":
        return "#inquiry-form"
    return "#contact"


@dataclass
class ResolvedIMChannel:
    channel_type: str
    account_id: str
    prefilled_text: str
    im_link: str
    display_text: str
    language: str
    country_code: str
    merchant_id: int
    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "channel_type": self.channel_type,
            "account_id": self.account_id,
            "prefilled_text": self.prefilled_text,
            "im_link": self.im_link,
            "display_text": self.display_text,
            "language": self.language,
            "country_code": self.country_code,
            "merchant_id": self.merchant_id,
        }


def _routing_to_resolved(
    routing: MerchantIMRouting,
    *,
    lang: str,
    cc: str,
    merchant_id: int,
) -> ResolvedIMChannel:
    """_routing_to_resolved。

    参数说明：
    :param routing: 参数 routing
    :param lang: 参数 lang
    :param cc: 参数 cc
    :param merchant_id: 参数 merchant_id
    :return: 返回处理结果。
    """
    return ResolvedIMChannel(
        channel_type=routing.channel_type,
        account_id=routing.account_id,
        prefilled_text=routing.prefilled_text or "",
        im_link=generate_im_link(routing.channel_type, routing.account_id),
        display_text=localized_channel_label(routing.channel_type, lang),
        language=lang,
        country_code=cc,
        merchant_id=merchant_id,
    )


def resolve_im_channels(
    db: Session,
    *,
    merchant_id: int,
    country_code: str,
    language: str | None = None,
) -> list[ResolvedIMChannel]:
    """P1-01：返回该国全部启用渠道 + 表单兜底。"""
    cc = country_code.strip().upper()[:2]
    lang = normalize_language(language, cc)
    rows = (
        db.query(MerchantIMRouting)
        .filter(
            MerchantIMRouting.merchant_id == merchant_id,
            MerchantIMRouting.country_code == cc,
            MerchantIMRouting.is_active.is_(True),
        )
        .order_by(MerchantIMRouting.id)
        .all()
    )
    channels = [_routing_to_resolved(r, lang=lang, cc=cc, merchant_id=merchant_id) for r in rows]
    # 中国大陆：仅微信 / QQ / 电话，不展示境外 IM 与表单兜底
    if cc == "CN":
        allowed = frozenset({"wechat", "qq", "phone"})
        return [c for c in channels if c.channel_type in allowed]
    seen = {c.channel_type for c in channels}
    if not channels:
        channels.append(
            ResolvedIMChannel(
                channel_type="live_chat",
                account_id="",
                prefilled_text="Hello! How can I help you?",
                im_link="#contact",
                display_text=localized_channel_label("live_chat", lang),
                language=lang,
                country_code=cc,
                merchant_id=merchant_id,
            )
        )
        seen.add("live_chat")
    if "form" not in seen:
        channels.append(
            ResolvedIMChannel(
                channel_type="form",
                account_id="",
                prefilled_text="",
                im_link="#inquiry-form",
                display_text=localized_channel_label("form", lang),
                language=lang,
                country_code=cc,
                merchant_id=merchant_id,
            )
        )
    return channels


def resolve_im_channel(
    db: Session,
    *,
    merchant_id: int,
    country_code: str,
    language: str | None = None,
) -> ResolvedIMChannel:
    """resolve_im_channel。

    参数说明：
    :param db: 参数 db
    :param merchant_id: 参数 merchant_id
    :param country_code: 参数 country_code
    :param language: 参数 language
    :return: 返回处理结果。
    """
    cc = country_code.strip().upper()[:2]
    channels = resolve_im_channels(
        db, merchant_id=merchant_id, country_code=cc, language=language
    )
    return channels[0]


def list_supported_languages() -> list[dict[str, str]]:
    """list_supported_languages。
    :return: 返回处理结果。
    """
    return [{"code": k, "name": v} for k, v in SUPPORTED_LANGUAGES.items()]
