# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SITE-DESIGN-01 · L-Pro 模板填槽与发布门禁。"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

L_PRO_TEMPLATE_ID = "premium-b2b-v1"
L_PRO_TEMPLATE_TIER = "L-Pro"

_CONTRACT_PATH = (
    Path(__file__).resolve().parents[3] / ".project" / "site-design-target.json"
)


def _slugify(value: str) -> str:
    """_slugify。

    参数说明：
    :param value: 参数 value
    :return: 返回处理结果。
    """
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "-", (value or "").strip().lower())
    text = text.strip("-")
    return text or "item"


def load_l_pro_contract() -> dict[str, Any]:
    """load_l_pro_contract。
    :return: 返回处理结果。
    """
    if not _CONTRACT_PATH.is_file():
        return {}
    try:
        data = json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def publish_gate_thresholds() -> dict[str, int]:
    """publish_gate_thresholds。
    :return: 返回处理结果。
    """
    contract = load_l_pro_contract()
    gate = contract.get("publish_gate") if isinstance(contract.get("publish_gate"), dict) else {}
    thresholds = gate.get("thresholds") if isinstance(gate.get("thresholds"), dict) else {}
    return {
        "min_products_with_images": int(thresholds.get("min_products_with_images") or 3),
        "min_spec_fields_per_sku": int(thresholds.get("min_spec_fields_per_sku") or 3),
    }


def is_l_pro_site_content(site_content: dict[str, Any] | None) -> bool:
    """is_l_pro_site_content。

    参数说明：
    :param site_content: 参数 site_content
    :return: 返回处理结果。
    """
    if not isinstance(site_content, dict):
        return False
    if site_content.get("templateTier") == L_PRO_TEMPLATE_TIER:
        return True
    visual = site_content.get("visualEditor")
    if isinstance(visual, dict) and visual.get("templateId") == L_PRO_TEMPLATE_ID:
        return True
    return site_content.get("templateId") == L_PRO_TEMPLATE_ID


def _default_specs_for_product(product_label: str, industry: str) -> list[dict[str, str]]:
    """_default_specs_for_product。

    参数说明：
    :param product_label: 参数 product_label
    :param industry: 参数 industry
    :return: 返回处理结果。
    """
    label = (product_label or industry or "Product").strip()
    short = label[:24]
    return [
        {"label": "Material", "value": f"{short} base material, export grade"},
        {"label": "Density / Grade", "value": "Custom density & thickness available"},
        {"label": "Application", "value": "Industrial insulation & construction export"},
    ]


def _primary_category(site_content: dict[str, Any], fallback: str) -> str:
    """_primary_category。

    参数说明：
    :param site_content: 参数 site_content
    :param fallback: 参数 fallback
    :return: 返回处理结果。
    """
    pages = site_content.get("pages") if isinstance(site_content.get("pages"), dict) else {}
    home = pages.get("home") if isinstance(pages.get("home"), dict) else {}
    categories = home.get("categories")
    if isinstance(categories, list) and categories:
        first = categories[0]
        if isinstance(first, dict) and first.get("name"):
            return str(first["name"])
        if isinstance(first, str):
            return first
    return fallback


def apply_l_pro_site_pass(
    site_content: dict[str, Any],
    *,
    product_name: str = "",
) -> dict[str, Any]:
    """Hermes 建站后处理：绑定 premium-b2b-v1、补全 L-Pro 槽位（非造版式）。"""
    out = copy.deepcopy(site_content)
    out["templateTier"] = L_PRO_TEMPLATE_TIER
    out["templateId"] = L_PRO_TEMPLATE_ID
    visual = out.get("visualEditor")
    if not isinstance(visual, dict):
        visual = {}
    visual = {**visual, "templateId": L_PRO_TEMPLATE_ID}
    out["visualEditor"] = visual
    pages = out.setdefault("pages", {})
    if not isinstance(pages, dict):
        pages = {}
        out["pages"] = pages

    category = _primary_category(out, product_name or "Products")
    products = pages.setdefault("products", {})
    if not isinstance(products, dict):
        products = {}
        pages["products"] = products

    raw_items = products.get("productItems")
    items: list[dict[str, Any]] = []
    if isinstance(raw_items, list):
        for row in raw_items:
            if isinstance(row, dict):
                items.append(dict(row))
            elif row:
                items.append({"name": str(row), "summary": ""})

    if not items:
        short = (product_name or "Product")[:20]
        items = [
            {
                "name": f"{short} Standard",
                "summary": f"Regular export spec {product_name}",
                "image": "",
            },
            {
                "name": f"{short} Enhanced",
                "summary": "Higher density / thickness for project buyers",
                "image": "",
            },
            {
                "name": f"{short} OEM Custom",
                "summary": "OEM/ODM branding and packaging",
                "image": "",
            },
        ]

    enriched: list[dict[str, Any]] = []
    for index, row in enumerate(items):
        name = str(row.get("name") or f"Product {index + 1}").strip()
        row["name"] = name
        row.setdefault("category", category)
        row.setdefault("slug", _slugify(str(row.get("slug") or row.get("sku") or name)))
        specs = row.get("specs")
        if not isinstance(specs, list) or len(specs) < publish_gate_thresholds()["min_spec_fields_per_sku"]:
            row["specs"] = _default_specs_for_product(name, product_name)
        enriched.append(row)

    products["productItems"] = enriched
    products["products"] = [str(it.get("name", "")).strip() for it in enriched if it.get("name")]
    downloads = pages.setdefault("downloads", {})
    if not isinstance(downloads, dict):
        downloads = {}
        pages["downloads"] = downloads
    if not isinstance(downloads.get("items"), list) or not downloads.get("items"):
        brand = ""
        brand_info = out.get("brand")
        if isinstance(brand_info, dict):
            brand = str(brand_info.get("name") or "").strip()
        downloads["title"] = str(downloads.get("title") or "Download Center")
        downloads["description"] = str(
            downloads.get("description") or "Brochures, datasheets and certificates",
        )
        downloads["items"] = [
            {
                "title": f"{brand or 'Company'} Profile",
                "url": "",
                "type": "brochure",
            },
            {
                "title": "Product Catalog & Spec Sheet",
                "url": "",
                "type": "datasheet",
            },
        ]

    about = pages.setdefault("about", {})
    if isinstance(about, dict) and not str(about.get("aboutText") or "").strip():
        about["aboutText"] = (
            f"We are a professional export manufacturer focused on {product_name or 'industrial products'}. "
            "Factory audit, bulk supply and project quotation supported."
        )

    meta = out.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["site_design_tier"] = L_PRO_TEMPLATE_TIER
        meta["site_design_contract"] = "SITE-DESIGN-01"

    return out


def _has_contact_channel(contact: dict[str, Any]) -> bool:
    """_has_contact_channel。

    参数说明：
    :param contact: 参数 contact
    :return: 返回处理结果。
    """
    for key in ("phone", "email", "whatsapp", "wechat", "qq"):
        if str(contact.get(key) or "").strip():
            return True
    return False


def _product_items(site_content: dict[str, Any]) -> list[dict[str, Any]]:
    """_product_items。

    参数说明：
    :param site_content: 参数 site_content
    :return: 返回处理结果。
    """
    pages = site_content.get("pages") if isinstance(site_content.get("pages"), dict) else {}
    products = pages.get("products") if isinstance(pages.get("products"), dict) else {}
    raw = products.get("productItems")
    if not isinstance(raw, list):
        return []
    return [dict(x) for x in raw if isinstance(x, dict)]


def validate_l_pro_publish_gate(
    site_content: dict[str, Any] | None,
    *,
    environment: str = "development",
) -> dict[str, Any]:
    """校验租户 site_content 是否达到 L-Pro 对外发布门槛。"""
    issues: list[dict[str, str]] = []
    thresholds = publish_gate_thresholds()
    if not isinstance(site_content, dict):
        issues.append({"severity": "P0", "check": "site_content", "detail": "missing site_content"})
        return _gate_result(issues, ready=False)

    if not is_l_pro_site_content(site_content):
        issues.append(
            {
                "severity": "P0",
                "check": "template",
                "detail": f"templateId must be {L_PRO_TEMPLATE_ID}",
            },
        )

    visual = site_content.get("visualEditor")
    if isinstance(visual, dict) and str(visual.get("html") or "").strip():
        issues.append(
            {
                "severity": "P1",
                "check": "visual_editor_html",
                "detail": "L-Pro should use premium shell; GrapesJS html should not be default face",
            },
        )

    items = _product_items(site_content)
    min_products = max(1, thresholds["min_products_with_images"])
    min_specs = max(1, thresholds["min_spec_fields_per_sku"])
    if len(items) < min_products:
        issues.append(
            {
                "severity": "P0",
                "check": "product_count",
                "detail": f"need>={min_products} productItems, got {len(items)}",
            },
        )

    with_images = [
        it for it in items if str(it.get("image") or "").strip() and not str(it.get("image")).startswith("data:")
    ]
    if len(with_images) < min_products:
        issues.append(
            {
                "severity": "P0",
                "check": "product_images",
                "detail": f"need>={min_products} products with image, got {len(with_images)}",
            },
        )

    for index, item in enumerate(items):
        specs = item.get("specs")
        spec_count = len(specs) if isinstance(specs, list) else 0
        if spec_count < min_specs:
            issues.append(
                {
                    "severity": "P0",
                    "check": "product_specs",
                    "detail": f"product[{index}] needs>={min_specs} specs, got {spec_count}",
                },
            )

    pages = site_content.get("pages") if isinstance(site_content.get("pages"), dict) else {}
    about = pages.get("about") if isinstance(pages.get("about"), dict) else {}
    if not str(about.get("aboutText") or "").strip():
        issues.append({"severity": "P0", "check": "about", "detail": "about.aboutText is empty"})

    contact = pages.get("contact") if isinstance(pages.get("contact"), dict) else {}
    if not _has_contact_channel(contact):
        issues.append(
            {
                "severity": "P0",
                "check": "contact",
                "detail": "need at least one contact channel (phone/email/whatsapp/wechat)",
            },
        )

    meta = site_content.get("meta")
    if isinstance(meta, dict):
        if meta.get("probe_mode") == "stub" or meta.get("mode") == "mock":
            issues.append({"severity": "P0", "check": "mock_mode", "detail": "site_content meta indicates mock/stub"})

    if environment == "production" and any(
        str(contact.get("email") or "").endswith("example.com")
        for _ in [contact]
    ):
        issues.append(
            {
                "severity": "P1",
                "check": "contact_placeholder",
                "detail": "production contact still uses example.com placeholder",
            },
        )

    p0 = [i for i in issues if i["severity"] == "P0"]
    return _gate_result(issues, ready=len(p0) == 0)


def _gate_result(issues: list[dict[str, str]], *, ready: bool) -> dict[str, Any]:
    """_gate_result。

    参数说明：
    :param issues: 参数 issues
    :param ready: 参数 ready
    :return: 返回处理结果。
    """
    p0 = [i for i in issues if i["severity"] == "P0"]
    p1 = [i for i in issues if i["severity"] == "P1"]
    return {
        "ok": ready,
        "publish_ready": ready,
        "p0": len(p0),
        "p1": len(p1),
        "issues": issues,
        "template_id": L_PRO_TEMPLATE_ID,
        "tier": L_PRO_TEMPLATE_TIER,
    }
