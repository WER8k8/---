# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""site_content CMS 数组字段多语种模板（stats / badges / milestones 等）。"""

from __future__ import annotations

from typing import Any


def build_array_i18n_pack(language: str, *, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """返回 { home: {stats,...}, about: {milestones} } 供写入 pages.*.i18n[lang]。"""
    builders = {
        "zh": _arrays_zh,
        "ar": _arrays_ar,
        "es": _arrays_es,
        "pt": _arrays_pt,
        "ru": _arrays_ru,
        "th": _arrays_th,
        "vi": _arrays_vi,
        "id": _arrays_id,
        "ms": _arrays_ms,
        "ja": _arrays_ja,
        "ko": _arrays_ko,
    }
    fn = builders.get(language)
    if not fn:
        return {}
    return fn(name=name, brand=brand, short=short)


def _arrays_zh(*, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """_arrays_zh。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "home": {
            "stats": [
                {"value": "20+", "label": "年行业经验"},
                {"value": "500+", "label": "服务项目"},
                {"value": "30+", "label": "专利与标准"},
                {"value": "40+", "label": "出口国家与地区"},
            ],
            "trustBadges": ["15+ 年经验", "OEM/ODM 定制", "工厂直供", "工程配套"],
            "applicationsTitle": "应用场景",
            "applications": [
                {"title": "屋面系统", "description": f"{name} 屋面保温系统，提升商业与工业建筑能效。"},
                {"title": "外墙保温", "description": f"外墙与幕墙 {name} 方案，防火节能。"},
                {"title": "暖通空调", "description": "风管、设备保温，降低热损与噪音。"},
                {"title": "工业设备", "description": f"高温设备、管道 {name} 保温防护。"},
            ],
            "solutions": [
                {"segment": "建筑", "title": "建筑工程", "description": f"墙体、屋面一体化 {name} 系统。"},
                {"segment": "工业", "title": "工业保温", "description": "工厂管道与设备可靠保温。"},
                {"segment": "暖通", "title": "暖通系统", "description": "中央空调风管与冷热源保温。"},
                {"segment": "船舶", "title": "船舶海工", "description": "船舱防火保温模块方案。"},
            ],
            "advantages": [
                {"title": "品质可控", "description": f"自有产线，{short}批次可追溯"},
                {"title": "定制生产", "description": "支持 OEM/ODM，按图纸打样"},
                {"title": "安装便捷", "description": "标准规格，缩短施工周期"},
                {"title": "批发工程", "description": "熟悉工程配套与批量供货"},
            ],
            "categories": [
                {"name": f"{short} 板材", "description": f"墙体屋面用 {name} 板"},
                {"name": f"{short} 卷材", "description": f"管道设备用 {name} 毡"},
                {"name": "OEM 定制", "description": "贴牌包装与规格定制"},
            ],
        },
        "about": {
            "milestones": [
                {"year": "2005", "title": "创立", "description": f"{brand} 成立，专注制造与贸易"},
                {"year": "2012", "title": "产能升级", "description": "扩建产线并设立质检实验室"},
                {"year": "2018", "title": "全国工程", "description": "服务国内工程与批发客户"},
                {"year": "2024", "title": "定制中心", "description": "OEM/ODM 与项目配套能力完善"},
            ],
        },
    }


def _arrays_en(*, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """_arrays_en。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "home": {
            "stats": [
                {"value": "20+", "label": "Years of Experience"},
                {"value": "500+", "label": "Projects Supplied"},
                {"value": "30+", "label": "Patents & Standards"},
                {"value": "40+", "label": "Export Countries"},
            ],
            "trustBadges": ["15+ Years Experience", "OEM/ODM Available", "Factory Direct", "Global Export"],
            "applicationsTitle": "Applications",
            "applications": [
                {"title": "Roof Systems", "description": f"{name} roofing insulation for commercial buildings."},
                {"title": "External Walls", "description": f"Facade and cavity wall {name} solutions."},
                {"title": "HVAC", "description": "Duct and equipment insulation for efficient HVAC."},
                {"title": "Industrial", "description": f"High-temperature {name} for plants and pipelines."},
            ],
            "solutions": [
                {"segment": "Building", "title": "Building & Construction", "description": f"Integrated {name} for walls and roofs."},
                {"segment": "Industrial", "title": "Industrial", "description": "Plant and pipeline thermal insulation."},
                {"segment": "HVAC", "title": "HVAC Systems", "description": "Air-handling and chiller insulation."},
                {"segment": "Marine", "title": "Marine & Offshore", "description": "Fire-safe marine compartment insulation."},
            ],
            "advantages": [
                {"title": "Quality Control", "description": f"In-house lines, traceable {short} batches."},
                {"title": "Custom OEM/ODM", "description": "Specs and packaging to your brand."},
                {"title": "Easy Install", "description": "Standard sizes for faster site work."},
                {"title": "Global Export", "description": "Export docs and multi-container shipping."},
            ],
        },
        "about": {
            "milestones": [
                {"year": "2005", "title": "Established", "description": f"{brand} founded for export manufacturing."},
                {"year": "2012", "title": "Capacity Upgrade", "description": "Expanded lines and QC laboratory."},
                {"year": "2018", "title": "Global Markets", "description": "Regular export to EU, MENA and ASEAN."},
                {"year": "2024", "title": "OEM Hub", "description": "Full custom branding for overseas buyers."},
            ],
        },
    }


def _arrays_ar(*, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """_arrays_ar。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    base = _arrays_en(name=name, brand=brand, short=short)
    base["home"]["stats"] = [
        {"value": "20+", "label": "سنوات خبرة"},
        {"value": "500+", "label": "مشروع"},
        {"value": "30+", "label": "براءات ومعايير"},
        {"value": "40+", "label": "دولة تصدير"},
    ]
    base["home"]["trustBadges"] = ["+15 سنة", "OEM/ODM", "مصنع مباشر", "تصدير عالمي"]
    base["home"]["applicationsTitle"] = "مجالات الاستخدام"
    return base


def _arrays_es(*, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """_arrays_es。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    base = _arrays_en(name=name, brand=brand, short=short)
    base["home"]["stats"] = [
        {"value": "20+", "label": "Años de experiencia"},
        {"value": "500+", "label": "Proyectos"},
        {"value": "30+", "label": "Patentes y normas"},
        {"value": "40+", "label": "Países de exportación"},
    ]
    base["home"]["trustBadges"] = ["+15 años", "OEM/ODM", "Fábrica directa", "Exportación global"]
    base["home"]["applicationsTitle"] = "Aplicaciones"
    return base


def _arrays_pt(*, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """_arrays_pt。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    base = _arrays_es(name=name, brand=brand, short=short)
    base["home"]["applicationsTitle"] = "Aplicações"
    return base


def _arrays_ru(*, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """_arrays_ru。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    base = _arrays_en(name=name, brand=brand, short=short)
    base["home"]["stats"] = [
        {"value": "20+", "label": "Лет опыта"},
        {"value": "500+", "label": "Проектов"},
        {"value": "30+", "label": "Патентов и стандартов"},
        {"value": "40+", "label": "Стран экспорта"},
    ]
    base["home"]["trustBadges"] = ["15+ лет", "OEM/ODM", "С завода", "Экспорт"]
    base["home"]["applicationsTitle"] = "Применение"
    return base


def _arrays_th(*, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """_arrays_th。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    base = _arrays_en(name=name, brand=brand, short=short)
    base["home"]["applicationsTitle"] = "การใช้งาน"
    base["home"]["trustBadges"] = ["15+ ปี", "OEM/ODM", "จากโรงงาน", "ส่งออก"]
    return base


def _arrays_vi(*, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """_arrays_vi。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    base = _arrays_en(name=name, brand=brand, short=short)
    base["home"]["applicationsTitle"] = "Ứng dụng"
    base["home"]["trustBadges"] = ["15+ năm", "OEM/ODM", "Xưởng trực tiếp", "Xuất khẩu"]
    return base


def _arrays_id(*, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """_arrays_id。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    base = _arrays_en(name=name, brand=brand, short=short)
    base["home"]["applicationsTitle"] = "Aplikasi"
    return base


def _arrays_ms(*, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """_arrays_ms。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    base = _arrays_en(name=name, brand=brand, short=short)
    base["home"]["applicationsTitle"] = "Aplikasi"
    return base


def _arrays_ja(*, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """_arrays_ja。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    base = _arrays_en(name=name, brand=brand, short=short)
    base["home"]["stats"] = [
        {"value": "20+", "label": "年の実績"},
        {"value": "500+", "label": "プロジェクト"},
        {"value": "30+", "label": "特許・規格"},
        {"value": "40+", "label": "輸出先国"},
    ]
    base["home"]["trustBadges"] = ["15年以上", "OEM/ODM", "工場直送", "グローバル輸出"]
    base["home"]["applicationsTitle"] = "用途"
    return base


def default_product_items_en(name: str, short: str, category: str) -> list[dict[str, Any]]:
    """英文基字段 productItems（出口站 canonical）。"""
    cat = category or short
    return [
        {
            "name": f"{short} Standard Grade",
            "summary": f"Regular spec {name} for wholesale and engineering projects",
            "image": "",
            "category": cat,
            "slug": "standard",
            "specs": [
                {"label": "Material", "value": f"{short} export grade"},
                {"label": "Density", "value": "Custom density available"},
                {"label": "Application", "value": "Wall / roof / industrial insulation"},
            ],
        },
        {
            "name": f"{short} Enhanced Grade",
            "summary": "Higher density/thickness options for export standards",
            "image": "",
            "category": cat,
            "slug": "enhanced",
            "specs": [
                {"label": "Material", "value": f"Enhanced {short}"},
                {"label": "Density", "value": "High-density option"},
                {"label": "Application", "value": "High-temp / fire-rated projects"},
            ],
        },
        {
            "name": f"{short} OEM Custom",
            "summary": "OEM/ODM with custom branding and packaging",
            "image": "",
            "category": cat,
            "slug": "oem-custom",
            "specs": [
                {"label": "Service", "value": "OEM / ODM branding"},
                {"label": "MOQ", "value": "Project-based quotation"},
                {"label": "Packaging", "value": "Custom label & export packing"},
            ],
        },
    ]


def default_product_items_zh(name: str, short: str, category: str) -> list[dict[str, Any]]:
    """中文 i18n productItems，slug 与英文基字段对齐。"""
    cat = category or short
    return [
        {
            "name": f"{short}标准款",
            "summary": f"常规规格 {name}，适合批发与工程项目",
            "image": "",
            "category": cat,
            "slug": "standard",
            "specs": [
                {"label": "Material", "value": f"{short} export grade"},
                {"label": "Density", "value": "Custom density available"},
                {"label": "Application", "value": "Wall / roof / industrial insulation"},
            ],
        },
        {
            "name": f"{short}加强款",
            "summary": "更高密度/厚度可选，满足出口高标准",
            "image": "",
            "category": cat,
            "slug": "enhanced",
            "specs": [
                {"label": "Material", "value": f"Enhanced {short}"},
                {"label": "Density", "value": "High-density option"},
                {"label": "Application", "value": "High-temp / fire-rated projects"},
            ],
        },
        {
            "name": f"{short}贴牌定制",
            "summary": "OEM/ODM，支持客户品牌与包装",
            "image": "",
            "category": cat,
            "slug": "oem-custom",
            "specs": [
                {"label": "Service", "value": "OEM / ODM branding"},
                {"label": "MOQ", "value": "Project-based quotation"},
                {"label": "Packaging", "value": "Custom label & export packing"},
            ],
        },
    ]


def _arrays_ko(*, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """_arrays_ko。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    base = _arrays_en(name=name, brand=brand, short=short)
    base["home"]["stats"] = [
        {"value": "20+", "label": "년 경력"},
        {"value": "500+", "label": "프로젝트"},
        {"value": "30+", "label": "특허·표준"},
        {"value": "40+", "label": "수출국"},
    ]
    base["home"]["trustBadges"] = ["15년+", "OEM/ODM", "공장 직송", "글로벌 수출"]
    base["home"]["applicationsTitle"] = "응용 분야"
    return base
