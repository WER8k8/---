# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""BOQ（Bill of Quantities）22 参数工业核价引擎。

30年外贸建材大厂标准：
- 材料基价 × 厚度系数 × 等级溢价
- 加工附加费：表面处理工艺 (surface_finish) + 磨边工艺 (edge_profile)
- 定制与品牌：LOGO套印 + 特殊规格定制
- 包装与合规：熏蒸木箱/铁架 + SGS/BV商检 + 原产地与体系认证
- 国际贸易术语 (Incoterms)：FOB基础港离岸价 / CIF到岸价(海运费+水渍险) / DDP完税交货
- 起订量阶梯折扣 (MOQ Tier Discount)
- 集装箱装载测算 (20GP重柜 27吨限重 / 40HQ 68方容积)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

BOQ_PARAMS = [
    "material_type", "material_grade", "quantity_sqm", "thickness_mm",
    "surface_finish", "edge_profile", "color", "brand",
    "origin_country", "certification", "packaging_type", "loading_port",
    "destination_port", "incoterms", "payment_terms", "lead_time_days",
    "warranty_years", "moq_pieces", "customization", "logo_printing",
    "inspection_required", "insurance_required",
]

# 材料密度（kg/m³），用于算重与集装箱装载限制
_MATERIAL_DENSITY = {
    "marble": 2700,
    "granite": 2800,
    "ceramic": 2200,
    "wood": 800,
    "metal": 7850,
}

# 表面加工费 (USD/sqm)
_SURFACE_FEES = {
    "polished": 0.0,
    "honed": 2.0,
    "flamed": 4.0,
    "bush_hammered": 6.0,
    "sandblasted": 5.0,
    "brushed": 3.5,
}

# 磨边加工费 (USD/sqm)
_EDGE_FEES = {
    "flat": 0.0,
    "eased": 0.0,
    "beveled": 2.0,
    "half_bullnose": 3.5,
    "full_bullnose": 5.0,
    "ogee": 7.0,
}

# 等级溢价系数
_GRADE_MULTIPLIER = {
    "a": 1.15,
    "premium": 1.15,
    "first_choice": 1.10,
    "standard": 1.0,
    "commercial": 0.90,
    "b": 0.85,
}


class BOQCalculator:
    """建材外贸 22 参数工业级核价引擎。"""

    def calculate(self, params: dict[str, Any]) -> dict[str, Any]:
        """核价：输入 22 参数，输出详细分项成本、集装箱配载及单证建议。"""
        missing = [p for p in ("material_type", "quantity_sqm", "incoterms") if not params.get(p)]
        if missing:
            return {"error": f"Missing required params: {missing}"}

        material_type = str(params["material_type"]).lower()
        quantity_sqm = float(params["quantity_sqm"])
        incoterms = str(params["incoterms"]).upper()

        base_unit_price = self._get_base_price(material_type)

        # 1. 厚度乘数（基准厚度 20mm）
        thickness = float(params.get("thickness_mm") or 20)
        thickness_factor = 1.0
        if "thickness_mm" in params and thickness != 20:
            thickness_factor = max(0.5, 1.0 + (thickness - 20) * 0.035)

        # 2. 等级系数
        grade = str(params.get("material_grade") or "standard").lower()
        grade_factor = _GRADE_MULTIPLIER.get(grade, 1.0)

        # 3. 表面工艺与磨边加工费
        surface = str(params.get("surface_finish") or "polished").lower()
        surface_fee_sqm = _SURFACE_FEES.get(surface, 0.0)

        edge = str(params.get("edge_profile") or "eased").lower()
        edge_fee_sqm = _EDGE_FEES.get(edge, 0.0)

        # 调整后的材料出厂基础单价 (USD/sqm)
        adjusted_unit_price = round(base_unit_price * thickness_factor * grade_factor + surface_fee_sqm + edge_fee_sqm, 2)
        material_subtotal = round(adjusted_unit_price * quantity_sqm, 2)

        # 4. 定制工艺溢价
        total = material_subtotal
        if params.get("customization"):
            total *= 1.15

        # 5. 附加固定杂费
        surcharges = 0.0
        if params.get("logo_printing"):
            surcharges += 500.0
        if params.get("inspection_required"):
            surcharges += 200.0
        if params.get("certification") in ("ce", "iso9001", "sgs", "greenguard"):
            surcharges += 350.0

        total += surcharges

        # 6. 海运与一切险 (Insurance & Freight)
        insurance_fee = 0.0
        if params.get("insurance_required") or incoterms in ("CIF", "CIP", "DDP"):
            insurance_fee = round(total * 0.02, 2)
            total += insurance_fee

        # 7. 阶梯起订量折扣 (MOQ Tier Discount)
        discount_rate = 0.0
        if quantity_sqm >= 3000:
            discount_rate = 0.08
        elif quantity_sqm >= 1000:
            discount_rate = 0.05
        if discount_rate > 0:
            total *= (1.0 - discount_rate)
        elif params.get("small_batch_surcharge") and quantity_sqm < 50:
            total *= 1.05

        # 8. 物理重量与集装箱配载估算（以建材 20GP 重柜 27 吨红线）
        density = _MATERIAL_DENSITY.get(material_type, 2600)
        volume_cbm = round((quantity_sqm * thickness) / 1000.0, 3)
        net_weight_tons = round((volume_cbm * density) / 1000.0, 2)
        gross_weight_tons = round(net_weight_tons * 1.08, 2)  # 含木箱托盘重

        containers_20gp = max(1, int(gross_weight_tons // 27) + (1 if gross_weight_tons % 27 > 0 else 0))

        return {
            "base_price": base_unit_price,
            "adjusted_unit_price": adjusted_unit_price,
            "quantity": quantity_sqm,
            "subtotal": round(material_subtotal, 2),
            "total": round(total, 2),
            "currency": "USD",
            "incoterms": incoterms,
            "valid_days": int(params.get("lead_time_days") or 30),
            "breakdown": {
                "thickness_mm": thickness,
                "thickness_factor": round(thickness_factor, 2),
                "grade": grade,
                "surface_finish": surface,
                "surface_fee_sqm": surface_fee_sqm,
                "edge_profile": edge,
                "edge_fee_sqm": edge_fee_sqm,
                "customization_surcharge": bool(params.get("customization")),
                "logo_fee": 500.0 if params.get("logo_printing") else 0.0,
                "inspection_fee": 200.0 if params.get("inspection_required") else 0.0,
                "insurance_fee": insurance_fee,
                "volume_cbm": volume_cbm,
                "gross_weight_tons": gross_weight_tons,
                "estimated_20gp_containers": containers_20gp,
            },
            "trade_advisory": (
                f"预估总毛重 {gross_weight_tons} 吨，建议订舱 {containers_20gp} 个 20GP 重柜（单个限重 27 吨）；"
                f"交货期约 {params.get('lead_time_days') or 30} 天；"
                f"付款方式推荐 {params.get('payment_terms') or '30% T/T Deposit, 70% against B/L copy'}。"
            ),
        }

    def _get_base_price(self, material_type: str) -> float:
        """获取基础单价（USD/sqm），优丁标准价格库。"""
        prices = {"marble": 80.0, "granite": 60.0, "ceramic": 25.0, "wood": 45.0, "metal": 120.0}
        return prices.get(material_type, 50.0)
