# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国内建材 RMB 工业核价与税费核算引擎 (Domestic Quote & VAT Engine)。

核心功能：
1. 增值税计算（13% 瓷砖/石材基准；3% 砂石骨料简易计税）
2. 增值税专票（税额单独列明供进项抵扣） vs 普票（含税包干价）
3. 表面加工费（抛光/哑光/仿古/火烧面）与板材厚度系数
4. 国内汽运/干线物流运距与吨位核算（元/㎡ 或 元/吨）
5. 针对工程采购商、区域代理商与批发商的分层折扣模型
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class DomesticQuoteService:
    """国内建材 RMB 核价服务。"""

    # 建材增值税基准税率
    VAT_RATES: Dict[str, float] = {
        "ceramic_tile": 0.13,     # 瓷砖：13%
        "natural_stone": 0.13,    # 天然石材：13%
        "sintered_stone": 0.13,   # 岩板大板：13%
        "sanitary_ware": 0.13,    # 卫浴五金：13%
        "aluminum_profile": 0.13, # 铝型材/门窗：13%
        "cement_product": 0.13,   # 水泥预制件：13%
        "sand_gravel": 0.03,      # 砂石骨料：3% (简易征收)
    }

    # 表面工艺加工附加费 (元/㎡)
    SURFACE_FEES: Dict[str, float] = {
        "polished": 0.0,       # 亮光/抛光（常规基准）
        "matte": 3.0,          # 哑光/柔光面
        "antique": 6.5,        # 仿古面/干粒刷抛
        "flamed": 8.0,         # 火烧面（石材防滑）
        "bush_hammered": 12.0, # 荔枝面/机刨面
        "leather": 15.0,       # 皮革面/丝绢面
    }

    # 买家类型专属折扣系数
    BUYER_TYPE_DISCOUNTS: Dict[str, float] = {
        "engineering": 0.92,   # 工程商集采 92 折
        "distributor": 0.88,   # 代理商 88 折
        "wholesaler": 0.85,    # 批发大仓 85 折
        "retail": 1.0,         # 散单终端无折扣
    }

    @classmethod
    def generate_rmb_quote(
        cls,
        *,
        product_category: str = "ceramic_tile",
        quantity_m2: float = 100.0,
        unit_price_rmb: float = 80.0,
        surface_treatment: str = "polished",
        thickness_mm: int = 10,
        vat_type: str = "general",
        logistics_km: float = 500.0,
        buyer_type: str = "engineering",
        brand_tier: str = "first_line",
    ) -> Dict[str, Any]:
        """生成详细的国内建材含税报价单。"""
        category_key = (product_category or "ceramic_tile").strip().lower()
        vat_rate = cls.VAT_RATES.get(category_key, 0.13)

        # 表面工艺费
        surf_key = (surface_treatment or "polished").strip().lower()
        surface_fee = cls.SURFACE_FEES.get(surf_key, 0.0)

        # 厚度系数：基准 10mm，每增加 2mm 加价 3%（原料与出材损耗）
        thickness_val = max(5, int(thickness_mm or 10))
        thickness_factor = 1.0 + max(0, (thickness_val - 10) / 2) * 0.03

        # 买家等级折扣
        b_type = (buyer_type or "engineering").strip().lower()
        discount = cls.BUYER_TYPE_DISCOUNTS.get(b_type, 0.92)

        # 出厂基价计算 (含工艺、厚度与折扣)
        base_unit_price = (unit_price_rmb * thickness_factor + surface_fee) * discount

        # 国内干线物流运费估算 (基准 0.015 元/㎡/公里，最低 4 元/㎡)
        km = max(0.0, float(logistics_km or 0.0))
        logistics_per_m2 = max(4.0, km * 0.015) if km > 0 else 0.0

        # 税前单价合计 (出厂含运)
        ex_vat_unit = base_unit_price + logistics_per_m2
        vat_amount_per_m2 = ex_vat_unit * vat_rate

        v_type = "special" if vat_type == "special" else "general"
        if v_type == "special":
            # 专票：税前金额 + 专票税额单独列示
            quoted_unit_price = ex_vat_unit
            total_net_amount = round(quoted_unit_price * quantity_m2, 2)
            total_vat_amount = round(vat_amount_per_m2 * quantity_m2, 2)
            grand_total = round(total_net_amount + total_vat_amount, 2)
            invoice_desc = f"增值税专用发票 (税率 {int(vat_rate * 100)}%)，税款可作为进项全额抵扣。"
        else:
            # 普票：包干含税到手价
            quoted_unit_price = round(ex_vat_unit + vat_amount_per_m2, 2)
            grand_total = round(quoted_unit_price * quantity_m2, 2)
            total_vat_amount = round((grand_total / (1 + vat_rate)) * vat_rate, 2)
            total_net_amount = round(grand_total - total_vat_amount, 2)
            invoice_desc = f"增值税普通发票 (含 {int(vat_rate * 100)}% 增值税)，包干到手开票。"

        # 付款账期与履约条款建议
        payment_terms = (
            "30% 预付款排产，60% 货到工地清点无误后付清，10% 质保金满三个月返还"
            if b_type == "engineering"
            else "现款现货：30% 预付款排单生产，发货前全额付清"
        )

        return {
            "currency": "CNY",
            "product_category": category_key,
            "quantity_m2": round(quantity_m2, 2),
            "buyer_type": b_type,
            "buyer_discount_rate": discount,
            "base_ex_factory_price": round(unit_price_rmb, 2),
            "thickness_mm": thickness_val,
            "thickness_factor": round(thickness_factor, 3),
            "surface_treatment": surf_key,
            "surface_fee_per_m2": surface_fee,
            "logistics_km": km,
            "logistics_fee_per_m2": round(logistics_per_m2, 2),
            "vat_rate": vat_rate,
            "vat_type": v_type,
            "unit_price_quoted": quoted_unit_price,
            "total_net_amount": total_net_amount,
            "total_vat_amount": total_vat_amount,
            "grand_total_rmb": grand_total,
            "invoice_description": invoice_desc,
            "payment_terms": payment_terms,
            "validity_days": 15,
            "lead_time_days": 12 if quantity_m2 <= 3000 else 20,
        }
