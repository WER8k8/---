"""公开站旺财 — 海关/出口问答（不暴露 Hermes/Agent 品牌）。"""

from __future__ import annotations

import re
from typing import Any, TYPE_CHECKING

from app.services.trade_intel_customs_service import enrich_blue_ocean_result
from app.services.trade_intel_data import (
    full_customs_catalog,
    list_category_catalog,
    load_category_aliases,
    load_category_index,
    load_country_aliases,
    load_country_index,
    search_customs,
)
from app.services.trade_intel_service import (
    DISCLAIMER,
    _resolve_category,
    _resolve_country,
    blue_ocean,
    export_feasibility,
    hs_lookup,
)
from app.services.visitor_locale_service import wangcai_disclaimer
from app.services.im_locale_service import normalize_language
from app.services.wangcai_reply_locale import wrap_wangcai_reply

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

_COUNTRY_EN: dict[str, str] = {
    "SA": "Saudi Arabia",
    "AE": "UAE",
    "QA": "Qatar",
    "KW": "Kuwait",
    "OM": "Oman",
    "BH": "Bahrain",
    "IQ": "Iraq",
    "US": "United States",
    "CA": "Canada",
    "MX": "Mexico",
    "BR": "Brazil",
    "AR": "Argentina",
    "CL": "Chile",
    "CO": "Colombia",
    "PE": "Peru",
    "DE": "Germany",
    "FR": "France",
    "GB": "United Kingdom",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands",
    "PL": "Poland",
    "RO": "Romania",
    "TR": "Turkey",
    "RU": "Russia",
    "UA": "Ukraine",
    "VN": "Vietnam",
    "ID": "Indonesia",
    "TH": "Thailand",
    "MY": "Malaysia",
    "SG": "Singapore",
    "PH": "Philippines",
    "MM": "Myanmar",
    "KH": "Cambodia",
    "LA": "Laos",
    "IN": "India",
    "PK": "Pakistan",
    "LK": "Sri Lanka",
    "BD": "Bangladesh",
    "JP": "Japan",
    "KR": "South Korea",
    "MN": "Mongolia",
    "AU": "Australia",
    "NZ": "New Zealand",
    "NG": "Nigeria",
    "EG": "Egypt",
    "ZA": "South Africa",
    "KE": "Kenya",
    "MA": "Morocco",
    "DZ": "Algeria",
}

_VERDICT_EN = {"go": "Good to explore", "caution": "Proceed with care", "hard": "High barrier"}


def _country_en(code: str) -> str:
    """_country_en。

    参数说明：
    :param code: 参数 code
    :return: 返回处理结果。
    """
    code = (code or "").upper()
    return _COUNTRY_EN.get(code) or load_country_index().get(code, {}).get("name_zh") or code


def _infer_category(message: str, product_hint: str | None) -> str:
    """_infer_category。

    参数说明：
    :param message: 参数 message
    :param product_hint: 参数 product_hint
    :return: 返回处理结果。
    """
    text = f"{message} {product_hint or ''}".strip()
    key = _resolve_category(text)
    if key:
        return key
    hint = (product_hint or "").strip()
    if hint:
        for alias, cat in load_category_aliases().items():
            if alias in hint:
                return cat
    return "insulation_board"


def _resolve_country_for_ask(message: str) -> str | None:
    """先匹配国名，避免把英文 we → WE 误判为国家码。"""
    for name, code in sorted(load_country_aliases().items(), key=lambda x: len(x[0]), reverse=True):
        if name.lower() in message.lower() or name in message:
            return code
    for code, en in _COUNTRY_EN.items():
        if en.lower() in message.lower():
            return code
    m = re.search(r"\b([A-Z]{2})\b", message.upper())
    if m:
        code = m.group(1)
        if code not in {"WE", "TO", "OR", "AT", "IS", "IT", "IN", "ON", "NO", "SO", "DO", "BE", "ME", "MY"}:
            return code
    return _resolve_country(message)


def detect_wangcai_intent(message: str) -> str:
    """detect_wangcai_intent。

    参数说明：
    :param message: 参数 message
    :return: 返回处理结果。
    """
    m = message.strip()
    lower = m.lower()
    if re.search(r"(海关|hs|编码|税号|harmonized|tariff code)", m, re.I):
        return "hs_lookup"
    if re.search(
        r"(全部品类|all categor|list all|top export market|海关数据|贸易数据|出口指数|"
        r"export index|trade data|customs data|statistics|统计)",
        m,
        re.I,
    ):
        return "customs_data"
    if re.search(
        r"(蓝海|哪个国家|哪国|哪些国家|好卖|best market|where to sell|top market|export to where)",
        m,
        re.I,
    ):
        return "blue_ocean"
    if re.search(
        r"(出口|export|ship to|send to|sell to|能发|能不能|can i|can we|feasible|compliance)",
        m,
        re.I,
    ):
        return "export_feasibility"
    if re.search(r"(help|what can|how|你好|您好|hi\b|hello)", lower):
        return "help"
    return "customs_data"


_PROMPT_LABELS: dict[str, dict[str, str]] = {
    "blue_ocean": {
        "zh": "哪些国家适合出口？",
        "en": "Best export markets?",
        "ar": "أفضل أسواق التصدير؟",
        "es": "¿Mejores mercados?",
        "pt": "Melhores mercados?",
        "ru": "Лучшие рынки?",
        "th": "ตลาดส่งออกที่ดี?",
        "vi": "Thị trường xuất khẩu?",
        "id": "Pasar ekspor terbaik?",
        "ms": "Pasaran eksport terbaik?",
        "ja": "輸出向け国は？",
        "ko": "수출 시장은?",
    },
    "us_feasibility": {
        "zh": "能出口美国吗？",
        "en": "Export to USA?",
        "ar": "التصدير للولايات المتحدة؟",
        "es": "¿Exportar a EE.UU.?",
        "pt": "Exportar para EUA?",
        "ru": "Экспорт в США?",
        "th": "ส่งออกสหรัฐ?",
        "vi": "Xuất khẩu Mỹ?",
        "ja": "米国へ輸出？",
        "ko": "미국 수출?",
    },
    "hs": {
        "zh": "海关编码多少？",
        "en": "HS code?",
        "ar": "رمز HS؟",
        "es": "¿Código HS?",
        "pt": "Código HS?",
        "ru": "Код HS?",
        "th": "รหัส HS?",
        "vi": "Mã HS?",
        "ja": "HSコード？",
        "ko": "HS 코드?",
    },
    "customs_vn": {
        "zh": "越南贸易数据",
        "en": "Trade data: Vietnam",
        "ar": "بيانات فيتنام",
        "es": "Datos: Vietnam",
        "vi": "Dữ liệu Việt Nam",
        "ja": "ベトナムデータ",
        "ko": "베트남 데이터",
    },
    "catalog": {
        "zh": "全部品类数据",
        "en": "All categories",
        "ar": "كل الفئات",
        "es": "Todas las categorías",
        "ja": "全カテゴリ",
        "ko": "전체 카테고리",
    },
}

_HELP_REPLIES: dict[str, dict[str, str]] = {
    "empty": {
        "zh": "可问我出口市场、HS 章节或海关统计 — 例如「岩棉板适合出口哪些国家？」",
        "en": "Ask me about export markets, HS chapters, or customs statistics — e.g. “Best markets for rock wool?”",
    },
    "help": {
        "zh": (
            "我可以帮您：\n"
            "· **出口可行性**（国家 + 产品）\n"
            "· **目标市场排名**（蓝海排序）\n"
            "· **HS 章节**查询\n"
            "· **海关贸易指数**（20 品类 × 50 国）\n\n"
            "点击下方快捷问题或直接输入。"
        ),
        "en": (
            "I can help with:\n"
            "· **Export feasibility** (country + product)\n"
            "· **Top markets** (blue-ocean ranking)\n"
            "· **HS chapter** lookup\n"
            "· **Customs trade index** for 20 categories × 50 countries\n\n"
            "Pick a quick question below or type your own."
        ),
    },
}


def _prompt_label(prompt_id: str, language: str | None) -> str:
    """_prompt_label。

    参数说明：
    :param prompt_id: 参数 prompt_id
    :param language: 参数 language
    :return: 返回处理结果。
    """
    lang = normalize_language(language, None)
    by_id = _PROMPT_LABELS.get(prompt_id, {})
    return by_id.get(lang) or by_id.get("en") or prompt_id


def _help_text(key: str, language: str | None) -> str:
    """_help_text。

    参数说明：
    :param key: 参数 key
    :param language: 参数 language
    :return: 返回处理结果。
    """
    lang = normalize_language(language, None)
    bucket = _HELP_REPLIES.get(key, {})
    return bucket.get(lang) or bucket.get("en") or ""


def suggested_prompts(
    product_hint: str | None = None,
    *,
    language: str | None = None,
) -> list[dict[str, str]]:
    """suggested_prompts。

    参数说明：
    :param product_hint: 参数 product_hint
    :param language: 参数 language
    :return: 返回处理结果。
    """
    product = product_hint or "our building materials"
    raw = [
        {
            "id": "blue_ocean",
            "label_en": "Best export markets?",
            "label_zh": "哪些国家适合出口？",
            "message": f"Where are the best export markets for {product}?",
        },
        {
            "id": "us_feasibility",
            "label_en": "Export to USA?",
            "label_zh": "能出口美国吗？",
            "message": f"Can we export {product} to the United States?",
        },
        {
            "id": "hs",
            "label_en": "HS code?",
            "label_zh": "海关编码多少？",
            "message": f"What HS chapter applies to {product}?",
        },
        {
            "id": "customs_vn",
            "label_en": "Trade data: Vietnam",
            "label_zh": "越南贸易数据",
            "message": "Show customs trade index for Vietnam",
        },
        {
            "id": "catalog",
            "label_en": "All categories",
            "label_zh": "全部品类数据",
            "message": "List all product categories and top export markets",
        },
    ]
    lang = normalize_language(language, None)
    for row in raw:
        row["label"] = _prompt_label(row["id"], lang)
    return raw


def _format_export_reply(fr: Any, *, product_hint: str | None) -> str:
    """_format_export_reply。

    参数说明：
    :param fr: 参数 fr
    :param product_hint: 参数 product_hint
    :return: 返回处理结果。
    """
    country = _country_en(fr.country_code)
    product = product_hint or fr.category
    verdict = _VERDICT_EN.get(fr.verdict, fr.verdict_label)
    certs = ", ".join(fr.certs[:4]) if fr.certs else "local import rules"
    lines = [
        f"**{product} → {country}**",
        f"Assessment: **{verdict}** (HS chapter {fr.hs_chapter}).",
        fr.summary.strip() if fr.summary else "",
        f"Typical docs: {certs}.",
    ]
    if fr.growth and fr.growth not in ("N/A", "unknown", ""):
        lines.append(f"Market signal: growth ~{fr.growth}, competition {fr.competition}.")
    lines.append(
        "Public statistics only — not live customs declarations. "
        "Tap WhatsApp or the contact form for a firm quote."
    )
    return "\n".join(line for line in lines if line)


def _format_blue_ocean(data: dict[str, Any], *, product_hint: str | None) -> str:
    """_format_blue_ocean。

    参数说明：
    :param data: 参数 data
    :param product_hint: 参数 product_hint
    :return: 返回处理结果。
    """
    product = product_hint or data.get("category") or "your product"
    lines = [f"Top markets for **{product}** (HS {data.get('hs_chapter')}):"]
    for i, rec in enumerate(data.get("recommendations") or [], 1):
        code = rec.get("country_code") or ""
        country = _country_en(code)
        idx = rec.get("customs_export_index")
        yoy = rec.get("customs_yoy_pct")
        verdict = _VERDICT_EN.get(rec.get("verdict") or "", rec.get("verdict") or "")
        extra = ""
        if idx is not None:
            extra = f" · export index {idx}"
            if yoy is not None:
                extra += f" (YoY {yoy:+.1f}%)"
        reason = (rec.get("reason") or "")[:100]
        lines.append(f"{i}. **{country}** — {verdict}{extra}. {reason}")
    lines.append("Need MOQ & specs? Message us — sample & datasheet available.")
    return "\n".join(lines)


def _format_hs(data: dict[str, Any], *, product_hint: str | None) -> str:
    """_format_hs。

    参数说明：
    :param data: 参数 data
    :param product_hint: 参数 product_hint
    :return: 返回处理结果。
    """
    product = product_hint or data.get("category") or "building materials"
    return (
        f"For **{product}**, start with **HS chapter {data.get('hs_chapter')}** "
        f"({data.get('category')}).\n"
        f"{data.get('note') or ''}\n"
        "Exact 6–10 digit codes depend on material, density & facing — send specs for confirmation."
    )


def _format_customs_overview(message: str, category_key: str) -> str:
    """_format_customs_overview。

    参数说明：
    :param message: 参数 message
    :param category_key: 参数 category_key
    :return: 返回处理结果。
    """
    if re.search(r"(all|全部|list|品类|categories)", message, re.I):
        catalog = list_category_catalog()
        lines = ["**Export market snapshot (public stats pilot):**"]
        for row in catalog[:20]:
            tops = ", ".join(
                f"{m.get('country_code')}({m.get('export_index')})"
                for m in (row.get("top_markets") or [])[:3]
            )
            lines.append(
                f"· {row.get('category_label')} HS{row.get('hs_chapter')}: {tops or '—'}"
            )
        lines.append(f"Full data: {len(catalog)} categories × 50 countries in our trade library.")
        return "\n".join(lines)

    hits = search_customs(query=message, category_key=category_key, limit=8)
    if not hits:
        hits = search_customs(category_key=category_key, limit=5)
    if not hits:
        return "No matching trade rows. Try a country name (e.g. Vietnam) or product type (e.g. rock wool)."

    lines = [f"**Trade index — {load_category_index().get(category_key, {}).get('category_label', category_key)}:**"]
    for h in hits:
        code = h.get("country_code") or ""
        lines.append(
            f"· {_country_en(code)}: index **{h.get('export_index')}**, "
            f"YoY {h.get('yoy_pct'):+.1f}% · verdict {h.get('verdict') or '—'}"
        )
    return "\n".join(lines)


def ask_wangcai(
    message: str,
    *,
    product_hint: str | None = None,
    db: "Session | None" = None,
    language: str | None = None,
) -> dict[str, Any]:
    """公开站旺财问答 — 基于全量海关种子 + M0 规则。"""
    lang = normalize_language(language, None)
    disclaimer = wangcai_disclaimer(language)
    def _pack(intent: str, reply: str, **extra: Any) -> dict[str, Any]:
        """_pack。

        参数说明：
        :param intent: 参数 intent
        :param reply: 参数 reply
        :param **extra: 参数 **extra
        :return: 返回处理结果。
        """
        return {
            "intent": intent,
            "reply": wrap_wangcai_reply(reply, language=lang, intent=intent),
            "disclaimer": disclaimer,
            "language": lang,
            **extra,
        }

    text = (message or "").strip()
    if not text:
        return _pack(
            "help",
            _help_text("empty", language),
            prompts=suggested_prompts(product_hint, language=language),
        )

    intent = detect_wangcai_intent(text)
    category_key = _infer_category(text, product_hint)
    if intent == "help":
        return _pack(
            intent,
            _help_text("help", language),
            prompts=suggested_prompts(product_hint, language=language),
            category_key=category_key,
        )

    if intent == "export_feasibility":
        country = _resolve_country_for_ask(text)
        fr = export_feasibility(
            text,
            category=category_key,
            country=country,
            db=db,
        )
        return _pack(
            intent,
            _format_export_reply(fr, product_hint=product_hint),
            tool_result=fr.to_dict(),
            category_key=category_key,
        )

    if intent == "blue_ocean":
        data = blue_ocean(text, category=category_key, db=db)
        data = enrich_blue_ocean_result(data, category_key)
        return _pack(
            intent,
            _format_blue_ocean(data, product_hint=product_hint),
            tool_result=data,
            category_key=category_key,
        )

    if intent == "hs_lookup":
        hs = hs_lookup(text or (product_hint or "insulation"))
        return _pack(
            intent,
            _format_hs(hs, product_hint=product_hint),
            tool_result=hs,
            category_key=category_key,
        )

    # customs_data
    country = _resolve_country_for_ask(text)
    hits = search_customs(
        query=text,
        category_key=category_key,
        country_code=country,
        limit=12,
    )
    reply = _format_customs_overview(text, category_key)
    return _pack(
        "customs_data",
        reply,
        tool_result={"hits": hits, "category_key": category_key},
        category_key=category_key,
    )


def public_customs_payload(*, category_key: str | None = None) -> dict[str, Any]:
    """public_customs_payload。

    参数说明：
    :param category_key: 参数 category_key
    :return: 返回处理结果。
    """
    if category_key:
        from app.services.trade_intel_data import customs_for_category
        row = customs_for_category(category_key)
        if not row:
            return {"found": False, "category_key": category_key}
        return {"found": True, **row, "disclaimer": full_customs_catalog()["disclaimer"]}
    return full_customs_catalog()
