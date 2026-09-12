"""旺财贸易问答回复 — 按访客语言加标题/脚注包装（数据层可仍为英文）。"""

from __future__ import annotations

from app.services.im_locale_service import normalize_language

_INTENT_HEADER: dict[str, dict[str, str]] = {
    "help": {
        "zh": "",
        "en": "",
    },
    "export_feasibility": {
        "zh": "【出口可行性参考】",
        "en": "Export feasibility (reference):",
    },
    "blue_ocean": {
        "zh": "【目标市场排名参考】",
        "en": "Top markets (reference):",
    },
    "hs_lookup": {
        "zh": "【HS 章节参考】",
        "en": "HS chapter (reference):",
    },
    "customs_data": {
        "zh": "【海关贸易指数参考】",
        "en": "Customs trade index (reference):",
    },
}

_REPLY_FOOTER: dict[str, str] = {
    "zh": "以上为公开统计数据；具体 MOQ、规格与报价请通过微信/QQ/电话联系我们确认。",
    "en": "Public statistics only — contact us for MOQ, specs and firm quotes.",
    "ar": "للمرجعية فقط — تواصل معنا للأسعار والمواصفات.",
    "es": "Solo referencia — contáctenos para cotización firme.",
    "ja": "参考データです。正式見積はお問い合わせください。",
    "ko": "참고용 공개 데이터입니다. 견적은 문의해 주세요.",
}

# 常见英文尾句 → 中文（避免大陆访客看到 WhatsApp 引导）
_TAIL_REPLACEMENTS_ZH: tuple[tuple[str, str], ...] = (
    (
        "Tap WhatsApp or the contact form for a firm quote.",
        "请通过页面联系方式或微信/QQ 获取正式报价。",
    ),
    (
        "Public statistics only — not live customs declarations.",
        "以上为公开统计样本，非实时报关单数据。",
    ),
    (
        "Need MOQ & specs? Message us — sample & datasheet available.",
        "需要 MOQ 与规格？欢迎留言，可提供样品与数据表。",
    ),
)


def wrap_wangcai_reply(reply: str, *, language: str | None, intent: str) -> str:
    """非 help 意图：加语言标题 + 脚注；中文替换常见英文尾句。"""
    text = (reply or "").strip()
    if not text or intent == "help":
        return text
    lang = normalize_language(language, None)
    header = (_INTENT_HEADER.get(intent) or {}).get(lang) or (_INTENT_HEADER.get(intent) or {}).get("en", "")
    footer = _REPLY_FOOTER.get(lang) or _REPLY_FOOTER["en"]
    if lang == "zh":
        for en, zh in _TAIL_REPLACEMENTS_ZH:
            text = text.replace(en, zh)
    parts = [p for p in (header, text, footer) if p]
    return "\n\n".join(parts)
