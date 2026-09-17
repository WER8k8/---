# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""site_content 按访客语言解析 i18n 覆盖层（Hero/About 等正文 + CMS 数组）。"""

from __future__ import annotations

from typing import Any

from app.services.im_locale_service import normalize_language

_HOME_STRING_FIELDS = (
    "title",
    "description",
    "seoDescription",
    "seoKeywords",
    "ctaPrimary",
    "ctaSecondary",
    "sectionTitle",
    "applicationsTitle",
    "inquiryHook",
)
_HOME_ARRAY_FIELDS = (
    "stats",
    "trustBadges",
    "applications",
    "solutions",
    "advantages",
    "categories",
)
_ABOUT_STRING_FIELDS = ("title", "aboutText", "mission", "vision", "capacitySummary")
_ABOUT_ARRAY_FIELDS = ("milestones",)
_BRAND_FIELDS = ("name", "tagline")
_PRODUCTS_FIELDS = ("title", "description")
_PRODUCTS_ARRAY_FIELDS = ("productItems",)


def _merge_i18n_block(page: dict[str, Any] | None, language: str) -> dict[str, Any]:
    """_merge_i18n_block。

    参数说明：
    :param page: 参数 page
    :param language: 参数 language
    :return: 返回处理结果。
    """
    if not isinstance(page, dict):
        return {}
    out = dict(page)
    i18n = page.get("i18n")
    if not isinstance(i18n, dict):
        return out
    overlay = i18n.get(language)
    if not isinstance(overlay, dict):
        overlay = i18n.get("en") if language != "en" else {}
    if isinstance(overlay, dict):
        for key, value in overlay.items():
            if key == "i18n":
                continue
            if value is None:
                continue
            if isinstance(value, str):
                if not value.strip():
                    continue
                out[key] = value
            elif isinstance(value, (list, dict)) and len(value) > 0:
                out[key] = value
    return out


def _pick_string_fields(page: dict[str, Any], fields: tuple[str, ...]) -> dict[str, str]:
    """_pick_string_fields。

    参数说明：
    :param page: 参数 page
    :param fields: 参数 fields
    :return: 返回处理结果。
    """
    picked: dict[str, str] = {}
    for field in fields:
        raw = page.get(field)
        if isinstance(raw, str) and raw.strip():
            picked[field] = raw.strip()
    return picked


def _pick_array_fields(page: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    """_pick_array_fields。

    参数说明：
    :param page: 参数 page
    :param fields: 参数 fields
    :return: 返回处理结果。
    """
    picked: dict[str, Any] = {}
    for field in fields:
        raw = page.get(field)
        if isinstance(raw, list) and raw:
            picked[field] = raw
    return picked


def localize_site_content_snippet(
    site_content: dict[str, Any] | None,
    language: str | None,
) -> dict[str, dict[str, Any]]:
    """
    从 tenant site_content 提取当前语言可见文案（优先 pages.*.i18n[lang]）。
    返回 { brand, home, about, products }，含字符串与数组字段。
    """
    if not isinstance(site_content, dict):
        return {}
    lang = normalize_language(language, None)
    pages = site_content.get("pages") if isinstance(site_content.get("pages"), dict) else {}
    brand_raw = site_content.get("brand") if isinstance(site_content.get("brand"), dict) else {}
    brand_merged = _merge_i18n_block(brand_raw, lang)
    home_merged = _merge_i18n_block(pages.get("home") if isinstance(pages.get("home"), dict) else {}, lang)
    about_merged = _merge_i18n_block(pages.get("about") if isinstance(pages.get("about"), dict) else {}, lang)
    products_merged = _merge_i18n_block(
        pages.get("products") if isinstance(pages.get("products"), dict) else {},
        lang,
    )
    brand = _pick_string_fields(brand_merged, _BRAND_FIELDS)
    home = {
        **_pick_string_fields(home_merged, _HOME_STRING_FIELDS),
        **_pick_array_fields(home_merged, _HOME_ARRAY_FIELDS),
    }
    about = {
        **_pick_string_fields(about_merged, _ABOUT_STRING_FIELDS),
        **_pick_array_fields(about_merged, _ABOUT_ARRAY_FIELDS),
    }
    products = {
        **_pick_string_fields(products_merged, _PRODUCTS_FIELDS),
        **_pick_array_fields(products_merged, _PRODUCTS_ARRAY_FIELDS),
    }
    out: dict[str, dict[str, Any]] = {}
    if brand:
        out["brand"] = brand
    if home:
        out["home"] = home
    if about:
        out["about"] = about
    if products:
        out["products"] = products
    return out
