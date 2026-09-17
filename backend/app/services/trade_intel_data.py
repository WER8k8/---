# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""出海参谋 JSON 数据加载（M0 矩阵 / M1 海关 / 市场数据源）。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _read_json(name: str) -> dict[str, Any]:
    """_read_json。

    参数说明：
    :param name: 参数 name
    :return: 返回处理结果。
    """
    path = _DATA_DIR / name
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_trade_matrix() -> list[dict[str, Any]]:
    """load_trade_matrix。
    :return: 返回处理结果。
    """
    doc = _read_json("trade_intel_matrix.json")
    rows = doc.get("matrix")
    if isinstance(rows, list) and rows:
        return rows
    return _LEGACY_MATRIX


_LEGACY_MATRIX: list[dict[str, Any]] = [
    {
        "category_key": "insulation_board",
        "category_label": "保温板",
        "hs_chapter": "6806",
        "countries": {
            "VN": {
                "verdict": "go",
                "growth": "+12%",
                "competition": "low",
                "certs": ["原产地证", "质检报告"],
                "notes": "东南亚需求增长，适合试点。",
            }
        },
    }
]


@lru_cache(maxsize=1)
def load_customs_public() -> dict[str, list[dict[str, Any]]]:
    """load_customs_public。
    :return: 返回处理结果。
    """
    doc = _read_json("trade_intel_customs_public.json")
    cats = doc.get("categories")
    if isinstance(cats, dict) and cats:
        return cats
    return {}


@lru_cache(maxsize=1)
def load_customs_meta() -> dict[str, str]:
    """load_customs_meta。
    :return: 返回处理结果。
    """
    doc = _read_json("trade_intel_customs_public.json")
    return {
        "disclaimer": str(doc.get("disclaimer") or ""),
        "default_source": str(doc.get("default_source") or ""),
    }


@lru_cache(maxsize=1)
def load_market_sources() -> dict[str, Any]:
    """load_market_sources。
    :return: 返回处理结果。
    """
    return _read_json("trade_intel_market_sources.json")


@lru_cache(maxsize=1)
def load_country_aliases() -> dict[str, str]:
    """load_country_aliases。
    :return: 返回处理结果。
    """
    doc = _read_json("trade_intel_countries.json")
    aliases: dict[str, str] = {}
    for row in doc.get("countries") or []:
        code = str(row.get("code") or "").upper()
        name = str(row.get("name_zh") or "")
        if code and name:
            aliases[name] = code
    # 常用简称
    aliases.update(
        {
            "沙特": "SA",
            "沙特阿拉伯": "SA",
            "美国": "US",
            "越南": "VN",
            "波兰": "PL",
            "印尼": "ID",
            "印度尼西亚": "ID",
            "阿联酋": "AE",
            "迪拜": "AE",
            "墨西哥": "MX",
            "德国": "DE",
            "法国": "FR",
            "英国": "GB",
            "泰国": "TH",
            "马来": "MY",
            "马来西亚": "MY",
            "印度": "IN",
            "卡塔尔": "QA",
            "挪威": "NO",
            "芬兰": "FI",
        }
    )
    return aliases


@lru_cache(maxsize=1)
def load_category_aliases() -> dict[str, str]:
    """load_category_aliases。
    :return: 返回处理结果。
    """
    doc = _read_json("trade_intel_categories.json")
    aliases: dict[str, str] = {
        "混凝土": "lightweight_concrete",
        "轻集料": "lightweight_concrete",
        "保温": "insulation_board",
        "保温板": "insulation_board",
        "墙板": "prefab_wall",
        "预制": "prefab_wall",
        "岩棉": "rock_wool",
        "玻璃棉": "glass_wool",
        "泡沫": "foam_insulation",
        "陶瓷纤维": "ceramic_fiber",
        "耐火砖": "refractory_brick",
        "水泥板": "cement_board",
        "石膏板": "gypsum_board",
        "防水": "waterproof_membrane",
        "钢结构": "steel_structure",
        "铝型材": "aluminum_profile",
        "玻璃": "glass_facade",
        "石材": "stone_tile",
        "木地板": "wood_flooring",
        "通风管道": "hvac_duct",
        "防火涂料": "fireproof_coating",
        "胶黏剂": "adhesive_sealant",
        "脚手架": "scaffolding",
    }
    for row in doc.get("categories") or []:
        key = row.get("category_key")
        label = row.get("category_label")
        if key and label:
            aliases[str(label)] = str(key)
    return aliases


def matrix_stats() -> dict[str, Any]:
    """matrix_stats。
    :return: 返回处理结果。
    """
    matrix = load_trade_matrix()
    countries = len(matrix[0]["countries"]) if matrix else 0
    doc = _read_json("trade_intel_matrix.json")
    return {
        "categories": len(matrix),
        "countries": countries,
        "total_rows": len(matrix) * countries,
        "matrix_spec": doc.get("matrix_spec") or f"{len(matrix)}×{countries}",
        "disclaimer": doc.get("disclaimer") or "",
    }


@lru_cache(maxsize=1)
def load_country_index() -> dict[str, dict[str, str]]:
    """load_country_index。
    :return: 返回处理结果。
    """
    doc = _read_json("trade_intel_countries.json")
    out: dict[str, dict[str, str]] = {}
    for row in doc.get("countries") or []:
        code = str(row.get("code") or "").upper()
        if not code:
            continue
        out[code] = {
            "name_zh": str(row.get("name_zh") or code),
            "region": str(row.get("region") or ""),
        }
    return out


@lru_cache(maxsize=1)
def load_category_index() -> dict[str, dict[str, str]]:
    """load_category_index。
    :return: 返回处理结果。
    """
    doc = _read_json("trade_intel_categories.json")
    out: dict[str, dict[str, str]] = {}
    for row in doc.get("categories") or []:
        key = str(row.get("category_key") or "")
        if not key:
            continue
        out[key] = {
            "category_label": str(row.get("category_label") or key),
            "hs_chapter": str(row.get("hs_chapter") or ""),
        }
    return out


def list_category_catalog() -> list[dict[str, Any]]:
    """list_category_catalog。
    :return: 返回处理结果。
    """
    idx = load_category_index()
    matrix = load_trade_matrix()
    customs = load_customs_public()
    rows: list[dict[str, Any]] = []
    for row in matrix:
        key = row["category_key"]
        meta = idx.get(key, {})
        top = sorted(
            customs.get(key) or [],
            key=lambda x: int(x.get("export_index") or 0),
            reverse=True,
        )[:5]
        rows.append(
            {
                "category_key": key,
                "category_label": meta.get("category_label") or row.get("category_label"),
                "hs_chapter": meta.get("hs_chapter") or row.get("hs_chapter"),
                "country_count": len(row.get("countries") or {}),
                "top_markets": top,
            }
        )
    return rows


def full_customs_catalog(*, include_matrix: bool = True) -> dict[str, Any]:
    """20 品类 × 50 国海关公开统计 + 可选 M0 规则摘要。"""
    matrix = load_trade_matrix()
    customs = load_customs_public()
    cat_idx = load_category_index()
    country_idx = load_country_index()
    meta = load_customs_meta()
    categories: list[dict[str, Any]] = []
    for row in matrix:
        key = row["category_key"]
        meta_cat = cat_idx.get(key, {})
        markets: list[dict[str, Any]] = []
        for m in customs.get(key) or []:
            code = str(m.get("country_code") or "").upper()
            cmeta = country_idx.get(code, {})
            item = dict(m)
            item["country_name_zh"] = cmeta.get("name_zh") or code
            item["region"] = cmeta.get("region") or ""
            if include_matrix:
                rule = (row.get("countries") or {}).get(code) or {}
                if rule:
                    item["verdict"] = rule.get("verdict")
                    item["growth"] = rule.get("growth")
                    item["competition"] = rule.get("competition")
            markets.append(item)
        categories.append(
            {
                "category_key": key,
                "category_label": meta_cat.get("category_label") or row.get("category_label"),
                "hs_chapter": meta_cat.get("hs_chapter") or row.get("hs_chapter"),
                "markets": markets,
            }
        )
    stats = matrix_stats()
    return {
        "matrix_spec": stats.get("matrix_spec"),
        "total_markets": stats.get("total_rows"),
        "disclaimer": meta.get("disclaimer") or stats.get("disclaimer"),
        "default_source": meta.get("default_source"),
        "categories": categories,
    }


def customs_for_category(category_key: str) -> dict[str, Any] | None:
    """customs_for_category。

    参数说明：
    :param category_key: 参数 category_key
    :return: 返回处理结果。
    """
    catalog = full_customs_catalog(include_matrix=True)
    for row in catalog.get("categories") or []:
        if row.get("category_key") == category_key:
            return row
    return None


def search_customs(
    *,
    query: str = "",
    category_key: str | None = None,
    country_code: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """search_customs。

    参数说明：
    :param query: 参数 query
    :param category_key: 参数 category_key
    :param country_code: 参数 country_code
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    q = (query or "").strip().lower()
    cc = (country_code or "").upper() or None
    catalog = full_customs_catalog(include_matrix=True)
    hits: list[dict[str, Any]] = []
    for cat in catalog.get("categories") or []:
        key = cat.get("category_key")
        if category_key and key != category_key:
            continue
        label = str(cat.get("category_label") or "")
        if q and q not in key and q not in label.lower():
            label_match = False
        else:
            label_match = True
        for m in cat.get("markets") or []:
            code = str(m.get("country_code") or "").upper()
            if cc and code != cc:
                continue
            name_zh = str(m.get("country_name_zh") or "")
            if q and not label_match:
                if q not in code.lower() and q not in name_zh:
                    continue
            hits.append(
                {
                    "category_key": key,
                    "category_label": label,
                    "hs_chapter": cat.get("hs_chapter"),
                    **m,
                }
            )
            if len(hits) >= limit:
                return hits
    return hits


def reload_trade_intel_cache() -> None:
    """reload_trade_intel_cache。
    :return: 返回处理结果。
    """
    load_trade_matrix.cache_clear()
    load_customs_public.cache_clear()
    load_customs_meta.cache_clear()
    load_market_sources.cache_clear()
    load_country_aliases.cache_clear()
    load_category_aliases.cache_clear()
    load_country_index.cache_clear()
    load_category_index.cache_clear()
