# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""BOQ（Bill of Quantities）22 参数核价引擎"""

BOQ_PARAMS = [
    "material_type", "material_grade", "quantity_sqm", "thickness_mm",
    "surface_finish", "edge_profile", "color", "brand",
    "origin_country", "certification", "packaging_type", "loading_port",
    "destination_port", "incoterms", "payment_terms", "lead_time_days",
    "warranty_years", "moq_pieces", "customization", "logo_printing",
    "inspection_required", "insurance_required",
]


class BOQCalculator:
    def calculate(self, params: dict) -> dict:
        """核价：输入 22 参数，输出报价"""
        missing = [p for p in ("material_type", "quantity_sqm", "incoterms") if not params.get(p)]
        if missing:
            return {"error": f"Missing required params: {missing}"}

        base_price = self._get_base_price(params["material_type"])
        quantity = params["quantity_sqm"]
        total = base_price * quantity

        if params.get("customization"):
            total *= 1.15
        if params.get("logo_printing"):
            total += 500
        if params.get("inspection_required"):
            total += 200
        if params.get("insurance_required"):
            total *= 1.02

        return {
            "base_price": base_price,
            "quantity": quantity,
            "subtotal": base_price * quantity,
            "total": round(total, 2),
            "currency": "USD",
            "valid_days": 30,
        }

    def _get_base_price(self, material_type: str) -> float:
        """获取基础单价（USD/sqm），后续接真实价格库"""
        prices = {"marble": 80, "granite": 60, "ceramic": 25, "wood": 45, "metal": 120}
        return prices.get(material_type, 50)
