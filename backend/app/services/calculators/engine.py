# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""工程计算器引擎 — 纯函数，无 Web 依赖，可单元测试。

包含：
- thermal_calc    热工计算（U值/热损失/保温厚度估算）
- fire_calc       防火计算（钢构件防火厚度估算）
- quantity_calc   数量/包装估算
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Optional


def _get_float(params: dict, key: str) -> Optional[float]:
    """实现 获取float 的功能。
    
    :param params: 参数 params（类型: dict）
    :param key: 参数 key（类型: str）
    :return: 返回 Optional[float] 结果
    """
    if key not in params or params[key] is None:
        return None
    try:
        return float(params[key])
    except (ValueError, TypeError):
        return None


def _get_int(params: dict, key: str) -> Optional[int]:
    """实现 获取int 的功能。
    
    :param params: 参数 params（类型: dict）
    :param key: 参数 key（类型: str）
    :return: 返回 Optional[int] 结果
    """
    if key not in params or params[key] is None:
        return None
    try:
        return int(params[key])
    except (ValueError, TypeError):
        return None


THERMAL_VERSION = "v1.0.0"

def thermal_calc(params: dict[str, Any]) -> dict[str, Any]:
    """实现 thermal计算 的功能。
    
    :param params: 参数 params（类型: dict[str, Any]）
    :return: 返回 dict[str, Any] 结果
    """
    thickness = _get_float(params, "thickness_mm")
    lam = _get_float(params, "thermal_conductivity")
    area = _get_float(params, "area_m2")
    delta_t = _get_float(params, "delta_t")
    target_u = _get_float(params, "target_u")
    ts = datetime.now().isoformat(timespec="seconds")
    if lam is None or lam <= 0:
        return {"code": 400, "error": "导热系数 λ 必须大于 0", "calculator": "thermal", "version": THERMAL_VERSION, "timestamp": ts}
    u_val = lam / (thickness / 1000) if thickness and thickness > 0 and lam > 0 else None
    r_val = (thickness / 1000) / lam if thickness and thickness > 0 and lam > 0 else None
    output = {"u_value": round(u_val, 4) if u_val else None, "u_value_unit": "W/(m²·K)", "thermal_resistance": round(r_val, 4) if r_val else None, "thermal_resistance_unit": "(m²·K)/W"}
    if u_val and area and delta_t:
        hl = u_val * area * delta_t / 1000
        output["heat_loss"] = round(hl, 2); output["heat_loss_unit"] = "kW"; output["heat_loss_label"] = f"热损失 ≈ {round(hl, 2)} kW"
    if target_u and target_u > 0 and lam > 0:
        rm = (lam / target_u) * 1000
        output["required_thickness_approx"] = round(rm, 1); output["required_thickness_unit"] = "mm"
        output["required_thickness_note"] = f"要达到 U={target_u} W/(m²·K)，约需 {round(rm, 1)} mm（λ={lam} W/(m·K)），需经结构设计验证"
    return {"code": 0, "calculator": "thermal", "version": THERMAL_VERSION, "timestamp": ts,
        "assumptions": ["计算基于稳态传热假设", "未考虑多层结构、热桥效应、边界条件", "实际工程设计需由专业工程师验证"],
        "input": {"thickness_mm": thickness, "thermal_conductivity": lam, "area_m2": area, "delta_t_c": delta_t, "target_u": target_u},
        "output": output}


FIRE_VERSION = "v1.0.0"
_SECTION_FACTOR_THICKNESS = {
    "low": {30: "0.5-1.0 mm", 60: "1.0-2.0 mm", 90: "2.0-3.0 mm", 120: "3.0-4.5 mm"},
    "medium": {30: "1.0-1.5 mm", 60: "2.0-3.0 mm", 90: "3.0-5.0 mm", 120: "4.0-6.0 mm"},
    "high": {30: "1.5-2.5 mm", 60: "3.0-5.0 mm", 90: "5.0-7.0 mm", 120: "6.0-9.0 mm"}}

def _section_category(hp_a: float) -> str:
    """实现 section分类 的功能。
    
    :param hp_a: 参数 hp_a（类型: float）
    :return: 返回 str 结果
    """
    return "low" if hp_a <= 100 else "medium" if hp_a <= 250 else "high"

def fire_calc(params: dict[str, Any]) -> dict[str, Any]:
    """实现 fire计算 的功能。
    
    :param params: 参数 params（类型: dict[str, Any]）
    :return: 返回 dict[str, Any] 结果
    """
    sf = _get_float(params, "section_factor")
    fr = _get_int(params, "fire_rating")
    steel_temp = _get_float(params, "steel_temp_limit")
    ts = datetime.now().isoformat(timespec="seconds")
    if not sf or not fr:
        return {"code": 400, "error": "截面系数和耐火等级为必填项", "calculator": "fire", "version": FIRE_VERSION, "timestamp": ts}
    cat = _section_category(sf)
    thickness = _SECTION_FACTOR_THICKNESS.get(cat, {}).get(fr, "数据不足，请咨询技术团队")
    return {"code": 0, "calculator": "fire", "version": FIRE_VERSION, "timestamp": ts,
        "assumptions": ["厚度估算基于典型膨胀型防火涂料参考数据", "实际厚度根据涂料型号、施工条件、结构类型不同而变化", "此结果不可替代正式防火设计", "钢构件临界温度默认 550°C"],
        "input": {"section_factor": sf, "section_factor_unit": "m-1", "section_factor_category": {"low": "低", "medium": "中", "high": "高"}.get(cat), "fire_rating": fr, "steel_temp_limit": steel_temp or 550},
        "output": {"candidate_thickness": thickness, "candidate_thickness_note": "该厚度范围为估算参考值。正式设计需参考型式检验报告并由专业工程师确认。"}}


QUANTITY_VERSION = "v1.0.0"

def quantity_calc(params: dict[str, Any]) -> dict[str, Any]:
    """实现 quantity计算 的功能。
    
    :param params: 参数 params（类型: dict[str, Any]）
    :return: 返回 dict[str, Any] 结果
    """
    area = _get_float(params, "area_m2")
    thickness = _get_float(params, "thickness_mm")
    den = _get_float(params, "density_kg_m3")
    wastage = _get_float(params, "wastage_pct") or 5.0
    pack_qty = _get_float(params, "packaging_qty_per_unit")
    ts = datetime.now().isoformat(timespec="seconds")
    if not area or area <= 0:
        return {"code": 400, "error": "面积必须大于 0", "calculator": "quantity", "version": QUANTITY_VERSION, "timestamp": ts}
    vol = area * (thickness / 1000) if thickness and thickness > 0 else None
    weight = vol * den if vol and den else None
    wv = vol * (wastage / 100) if vol else None
    vt = vol + wv if vol is not None and wv is not None else vol
    packs = math.ceil(area / pack_qty) if pack_qty and pack_qty > 0 else None
    o = {"volume": round(vol, 2) if vol else None, "volume_unit": "m3", "weight": round(weight, 2) if weight else None, "weight_unit": "kg"}
    if weight: o["weight_label"] = f"approx {round(weight, 2)} kg"
    if vt: o["volume_with_wastage"] = round(vt, 2); o["volume_with_wastage_unit"] = "m3"; o["wastage_applied"] = f"{wastage}%"
    if packs: o["packages"] = packs; o["packages_label"] = f"about {packs} packages"
    return {"code": 0, "calculator": "quantity", "version": QUANTITY_VERSION, "timestamp": ts,
        "assumptions": ["体积按均匀厚度计算，未考虑表面不规则性", "损耗率默认 5%", "包装估算基于标准包装尺寸"],
        "input": {"area_m2": area, "thickness_mm": thickness, "density_kg_m3": den, "wastage_pct": wastage, "packaging_qty_per_unit": pack_qty},
        "output": o}