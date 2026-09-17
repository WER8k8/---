# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SITE-JTBD-01 · B2B 建站思维层（与 frontend industryPresets.ts 对齐）。"""

from __future__ import annotations

import copy
import re
from typing import Any

B2B_JTBD_PRESET: dict[str, Any] = {
    "primary_promise": (
        "One clear outcome site-wide: scoped quote, gated sampling, production you can audit."
    ),
    "heroTitle": "Quote, sample, and scale — structured for buyers with a job to do",
    "heroDescription": (
        "Buyers arrive with drawings and deadlines, not curiosity tours. "
        "We answer by project stage: feasibility → sample → pilot → volume."
    ),
    "inquiryHook": (
        "Send specs or drawings — we reply with scope, lead-time assumptions, and next steps."
    ),
    "ctaPrimary": "Request Quote",
    "serviceStages": [
        {
            "stage": "01",
            "title": "RFQ & feasibility",
            "description": "Material, tolerance, MOQ, and process fit review.",
        },
        {
            "stage": "02",
            "title": "Prototype / sample",
            "description": "First articles, test reports, packaging sign-off.",
        },
        {
            "stage": "03",
            "title": "Pilot batch",
            "description": "Small-run validation before volume commitment.",
        },
        {
            "stage": "04",
            "title": "Volume production",
            "description": "Stable QC cadence, docs, and shipment rhythm.",
        },
    ],
    "knowledgeTopics": [
        {
            "title": "How to package an RFQ buyers can quote fast",
            "hook": "Drawings, qty, destination, cert needs",
        },
        {
            "title": "Sample gate vs pilot batch: when to commit tooling",
            "hook": "Align buyer expectations with shop floor",
        },
        {
            "title": "Export documentation buyers expect on first order",
            "hook": "CO, HS codes, inspection booking",
        },
    ],
    "trustBadges": [
        "Stage-gated workflow",
        "Audit-ready QC",
        "OEM / ODM",
        "Export documentation",
    ],
    "stats": [
        {"value": "RFQ→Scope", "label": "Structured quote workflow"},
        {"value": "Sample gate", "label": "Before volume commit"},
        {"value": "QC trail", "label": "Reports tied to batch"},
        {"value": "One CTA", "label": "Same promise everywhere"},
    ],
    "solutions": [
        {"segment": "New product launch", "title": "DFM review + first-article program"},
        {"segment": "Cost-down redesign", "title": "Material/process alternatives with tolerance map"},
        {"segment": "Urgent replacement", "title": "Reverse spec match + expedited sampling"},
    ],
    "advantages": [
        {
            "title": "Outcome-first pages",
            "description": "Hero, stats, and CTA repeat the same buyer promise.",
        },
        {
            "title": "Evidence over slogans",
            "description": "Certs, cases, and process gates — not adjective walls.",
        },
    ],
    "sectionTitle": "Why buyers shortlist us",
    "sectionDesc": (
        "Capabilities mapped to how overseas buyers actually decide — "
        "not how our warehouse is organized."
    ),
}

PRECISION_MANUFACTURING_JTBD: dict[str, Any] = {
    **B2B_JTBD_PRESET,
    "heroTitle": "From drawing to shipped parts — CNC, molding, sheet metal & additive",
    "heroDescription": (
        "Machining, molding, fabrication, and 3D print programs under one "
        "RFQ → sample → production path."
    ),
    "solutions": [
        {"segment": "CNC machining", "title": "Aluminum, steel & stainless precision parts"},
        {"segment": "Injection molding", "title": "Tooling program + molded components"},
        {"segment": "Sheet metal", "title": "Laser, bend, weld & powder-coat assemblies"},
        {"segment": "3D printing", "title": "Rapid prototypes → small-series production"},
    ],
    "knowledgeTopics": [
        {
            "title": "CNC tolerance bands that affect quote speed",
            "hook": "GD&T packages buyers should attach",
        },
        {
            "title": "Injection mold steel vs aluminum tooling trade-offs",
            "hook": "When to gate with T0/T1 shots",
        },
        {
            "title": "Sheet metal bend radii & PEM hardware pitfalls",
            "hook": "DFM notes for overseas buyers",
        },
        {
            "title": "Additive vs subtractive for first article",
            "hook": "Material, finish, and MOQ fit",
        },
    ],
    "trustBadges": [
        "CNC · Molding · Sheet metal · 3DP",
        "First-article reports",
        "OEM programs",
        "Export packing",
    ],
}

_TEMPLATE_INDUSTRY: dict[str, str] = {
    "premium-b2b-v1": "export",
    "insulation-classic": "insulation",
    "building-modern": "lightweight",
    "export-pro": "export",
    "fireproof-safety": "fireproof",
    "rubber-insulation": "rubber",
    "steel-structure": "steel",
    "ceramic-stone": "ceramic",
    "hvac-duct": "hvac",
}

_PRECISION_INDUSTRIES = frozenset({"steel", "precision-manufacturing"})

_GENERIC_HERO_MARKERS = (
    "您的公司",
    "专业制造商",
    "专业建材制造商",
    "Professional Manufacturer",
    "Manufacturing Partner",
    "Manufacturer, Supplier & Factory",
)


def _merge_list(current: Any, preset: list[Any]) -> list[Any]:
    """_merge_list。

    参数说明：
    :param current: 参数 current
    :param preset: 参数 preset
    :return: 返回处理结果。
    """
    if isinstance(current, list) and current:
        return current
    return copy.deepcopy(preset)


def _merge_scalar(current: Any, preset: str) -> str:
    """_merge_scalar。

    参数说明：
    :param current: 参数 current
    :param preset: 参数 preset
    :return: 返回处理结果。
    """
    cur = str(current or "").strip()
    return cur or preset


def _is_generic_hero_title(title: Any) -> bool:
    """_is_generic_hero_title。

    参数说明：
    :param title: 参数 title
    :return: 返回处理结果。
    """
    t = str(title or "").strip()
    if not t:
        return True
    if t in _GENERIC_HERO_MARKERS:
        return True
    if re.search(r"^专业.+制造商", t):
        return True
    if re.search(r"professional\s+manufacturer", t, re.I):
        return True
    if re.search(r"manufacturer,\s*supplier\s*&\s*factory", t, re.I):
        return True
    return False


def resolve_jtbd_preset(site_content: dict[str, Any]) -> dict[str, Any]:
    """resolve_jtbd_preset。

    参数说明：
    :param site_content: 参数 site_content
    :return: 返回处理结果。
    """
    template_id = str(site_content.get("templateId") or "premium-b2b-v1")
    industry = _TEMPLATE_INDUSTRY.get(template_id, "export")
    meta_industry = site_content.get("meta") if isinstance(site_content.get("meta"), dict) else {}
    if isinstance(meta_industry, dict) and meta_industry.get("industry"):
        industry = str(meta_industry["industry"])
    if industry in _PRECISION_INDUSTRIES:
        return copy.deepcopy(PRECISION_MANUFACTURING_JTBD)
    return copy.deepcopy(B2B_JTBD_PRESET)


def apply_jtbd_site_pass(site_content: dict[str, Any]) -> dict[str, Any]:
    """补全 pages.home JTBD 字段（仅填空，不覆盖租户已编辑内容）。"""
    if not isinstance(site_content, dict):
        return site_content

    out = copy.deepcopy(site_content)
    jtbd = resolve_jtbd_preset(out)
    pages = out.setdefault("pages", {})
    if not isinstance(pages, dict):
        pages = {}
        out["pages"] = pages
    home = pages.setdefault("home", {})
    if not isinstance(home, dict):
        home = {}
        pages["home"] = home

    home["primary_promise"] = _merge_scalar(home.get("primary_promise"), jtbd["primary_promise"])
    if _is_generic_hero_title(home.get("title")):
        home["title"] = jtbd["heroTitle"]
    if not str(home.get("description") or "").strip():
        home["description"] = jtbd["heroDescription"]
    home["inquiryHook"] = _merge_scalar(home.get("inquiryHook"), jtbd["inquiryHook"])
    if not str(home.get("ctaPrimary") or "").strip():
        home["ctaPrimary"] = jtbd["ctaPrimary"]
    home["serviceStages"] = _merge_list(home.get("serviceStages"), jtbd["serviceStages"])
    home["knowledgeTopics"] = _merge_list(home.get("knowledgeTopics"), jtbd["knowledgeTopics"])
    home["trustBadges"] = _merge_list(home.get("trustBadges"), jtbd["trustBadges"])
    home["stats"] = _merge_list(home.get("stats"), jtbd["stats"])
    home["solutions"] = _merge_list(home.get("solutions"), jtbd["solutions"])
    home["advantages"] = _merge_list(home.get("advantages"), jtbd["advantages"])
    if not home.get("sectionDesc"):
        home["sectionDesc"] = jtbd["sectionDesc"]
    if not home.get("sectionTitle"):
        home["sectionTitle"] = jtbd["sectionTitle"]

    brand = out.setdefault("brand", {})
    if not isinstance(brand, dict):
        brand = {}
        out["brand"] = brand
    tagline = str(brand.get("tagline") or "").strip()
    if not tagline or re.search(r"专业.+制造商", tagline):
        brand["tagline"] = home["primary_promise"]

    meta = out.setdefault("meta", {})
    if isinstance(meta, dict):
        template_id = str(out.get("templateId") or "premium-b2b-v1")
        industry = _TEMPLATE_INDUSTRY.get(template_id, "export")
        skin = "precision" if industry in _PRECISION_INDUSTRIES else "b2b"
        meta["jtbd_applied"] = "SITE-JTBD-01"
        meta["jtbd_skin"] = skin

    return out
