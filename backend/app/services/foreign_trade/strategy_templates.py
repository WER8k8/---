# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""议价策略模板 —— 按 Incoterms 提供差异化报价参数与折扣策略。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── 策略参数 ──────────────────────────────────────────────────
@dataclass
class StrategyParams:
    """单条策略的完整报价参数。"""
    # Incoterms 类型
    incoterms: str

    # 基础利润率（%）
    base_profit_margin_pct: float

    # 首轮可让步上限（%）
    first_round_discount_pct: float

    # 最大自动授权折扣（%）
    max_auto_discount_pct: float

    # 底价利润率（成本保底，%）
    floor_margin_pct: float

    # MOQ 阶梯（(最小数量, 额外折扣%)）
    moq_discounts: List[Dict[str, Any]] = field(default_factory=list)

    # 样品单特殊标记（True = 样品单不适用大宗折扣）
    sample_mode: bool = False

    # 额外条款（如运费补贴上限、保修期等）
    extra_terms: Dict[str, Any] = field(default_factory=dict)

    def build_quote_params(
        self,
        *,
        base_cost: float,
        quantity: int,
        unit_price_override: Optional[float] = None,
    ) -> Dict[str, Any]:
        """根据当前谈判上下文生成报价参数字典。"""
        margin = self.base_profit_margin_pct
        quoted_price = unit_price_override or round(
            base_cost * (1.0 + margin / 100.0), 2
        )
        floor_price = round(base_cost * (1.0 + self.floor_margin_pct / 100.0), 2)

        # MOQ 联动折扣
        moq_extra = 0.0
        for entry in sorted(self.moq_discounts, key=lambda e: e["min_qty"], reverse=True):
            if quantity >= int(entry["min_qty"]):
                moq_extra = float(entry.get("discount_pct", 0.0))
                break

        # 样品单：不叠加 MOQ 折扣
        if self.sample_mode and quantity < 10:
            moq_extra = 0.0

        total_discount = min(moq_extra + self.first_round_discount_pct, 100.0)
        final_price = round(quoted_price * (1.0 - total_discount / 100.0), 2)
        final_price = max(final_price, floor_price)  # 底价保护

        return {
            "incoterms": self.incoterms,
            "quoted_unit_price": quoted_price,
            "final_unit_price": final_price,
            "floor_price": floor_price,
            "base_cost": base_cost,
            "profit_margin_pct": margin,
            "moq_extra_discount_pct": moq_extra,
            "first_round_discount_pct": self.first_round_discount_pct,
            "max_auto_discount_pct": self.max_auto_discount_pct,
            "total_discount_pct": round((1.0 - final_price / quoted_price) * 100, 2),
            "sample_mode": self.sample_mode,
            "extra_terms": self.extra_terms,
        }


# ── 内置策略模板 ──────────────────────────────────────────────

# FOB 策略：卖方负责到装运港，买方承担海运费与保险
for_fo_strategy = StrategyParams(
    incoterms="FOB Shenzhen",
    base_profit_margin_pct=15.0,
    first_round_discount_pct=0.0,       # 首轮零折扣，强调品质
    max_auto_discount_pct=5.0,
    floor_margin_pct=8.0,
    moq_discounts=[
        {"min_qty": 1000, "discount_pct": 3.0},
        {"min_qty": 500, "discount_pct": 2.0},
        {"min_qty": 100, "discount_pct": 1.0},
    ],
    extra_terms={
        "port_of_loading": "Shenzhen, China",
        "lead_time_days": 25,
        "warranty_months": 12,
        "sample_order_extra_lead_days": 5,
    },
)

# CIF 策略：卖方承担运费+保险至目的港，价格含海运费
cif_strategy = StrategyParams(
    incoterms="CIF Rotterdam",
    base_profit_margin_pct=20.0,        # 含运费，利润率略高
    first_round_discount_pct=2.0,       # 首轮可让 2%
    max_auto_discount_pct=8.0,
    floor_margin_pct=10.0,
    moq_discounts=[
        {"min_qty": 500, "discount_pct": 3.0},
        {"min_qty": 200, "discount_pct": 2.0},
        {"min_qty": 50, "discount_pct": 1.0},
    ],
    extra_terms={
        "port_of_loading": "Shenzhen, China",
        "port_of_discharge": "Rotterdam, Netherlands",
        "estimated_freight_usd": 2500.0,
        "insurance_pct": 1.1,
        "lead_time_days": 30,
        "warranty_months": 18,
    },
)

# DDP 策略：卖方负责到买方门，含关税，价格最高
ddp_strategy = StrategyParams(
    incoterms="DDP Amsterdam",
    base_profit_margin_pct=25.0,        # 含运费+关税，溢价最高
    first_round_discount_pct=1.0,
    max_auto_discount_pct=6.0,
    floor_margin_pct=12.0,
    moq_discounts=[
        {"min_qty": 300, "discount_pct": 2.5},
        {"min_qty": 100, "discount_pct": 1.5},
        {"min_qty": 30, "discount_pct": 0.5},
    ],
    extra_terms={
        "port_of_loading": "Shenzhen, China",
        "port_of_discharge": "Amsterdam, Netherlands",
        "estimated_duty_pct": 6.5,
        "estimated_freight_usd": 3200.0,
        "lead_time_days": 35,
        "warranty_months": 24,
        "customs_clearance_included": True,
    },
)


# ── 策略注册表 ────────────────────────────────────────────────
STRATEGY_REGISTRY: Dict[str, StrategyParams] = {
    "FOB": for_fo_strategy,
    "CIF": cif_strategy,
    "DDP": ddp_strategy,
}


def get_strategy(incoterms_key: str) -> StrategyParams:
    """按 Incoterms 键获取策略模板，未命中时回退到 FOB 默认策略。"""
    return STRATEGY_REGISTRY.get(incoterms_key.upper(), for_fo_strategy)


def list_strategies() -> List[str]:
    """返回所有可用策略的 Incoterms 键列表。"""
    return list(STRATEGY_REGISTRY.keys())
