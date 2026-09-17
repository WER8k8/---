# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI-M1：海关公开统计试点数据（带来源标注，非实时报关 API）。"""

from __future__ import annotations

from typing import Any

from app.services.trade_intel_data import load_customs_meta, load_customs_public

_DEFAULT_SOURCE = load_customs_meta().get("default_source") or (
    "规则矩阵 M0 + 海关公开统计 M1（试点，需法务确认对外表述）"
)
_DEFAULT_DISCLAIMER = load_customs_meta().get("disclaimer") or (
    "指数为内部整理的公开统计试点，不代表实时报关数据；对外宣传须人工复核。"
)


def _customs_rows(category_key: str) -> list[dict[str, Any]]:
    """_customs_rows。

    参数说明：
    :param category_key: 参数 category_key
    :return: 返回处理结果。
    """
    data = load_customs_public()
    return list(data.get(category_key) or data.get("insulation_board") or [])


def customs_stats_for_category(category_key: str) -> dict[str, Any]:
    """customs_stats_for_category。

    参数说明：
    :param category_key: 参数 category_key
    :return: 返回处理结果。
    """
    rows = _customs_rows(category_key)
    return {
        "category_key": category_key,
        "items": rows,
        "disclaimer": _DEFAULT_DISCLAIMER,
        "default_source": _DEFAULT_SOURCE,
    }


def enrich_blue_ocean_result(result: dict[str, Any], category_key: str) -> dict[str, Any]:
    """为蓝海 Top3 附加海关公开统计字段与来源。"""
    customs = {r["country_code"]: r for r in _customs_rows(category_key)}
    sources = list(result.get("sources") or [])
    if customs:
        sources.append(_DEFAULT_SOURCE)
    for rec in result.get("recommendations") or []:
        code = rec.get("country_code")
        row = customs.get(code)
        if not row:
            continue
        rec["customs_export_index"] = row["export_index"]
        rec["customs_yoy_pct"] = row["yoy_pct"]
        rec["customs_source"] = row["source"]
        rec["customs_source_url"] = row["source_url"]
        reason = rec.get("reason") or ""
        rec["reason"] = (
            f"{reason} · 出口景气{row['export_index']} YoY{row['yoy_pct']:+.1f}%"
        ).strip(" · ")
    result["sources"] = sources
    result["customs_m1"] = bool(customs)
    return result
