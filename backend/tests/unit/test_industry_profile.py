# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Industry Profile 参数化测试（修正设计稿 模块2 / 法典第一章验收）。

锁定语义：
- 未传 profile → 引擎内置建材默认，结果与历史完全一致（零漂移）；
- 传入自定义 profile（机械行业：钢结构件基价/密度覆盖）→ 计算走覆盖值；
- 服务层 get_active_profile 取 active 最大版本；seed 幂等。
"""
from __future__ import annotations

from app.services.boq_calculator import BOQCalculator

BASE_PARAMS = {
    "material_type": "ceramic",
    "quantity_sqm": 1000,
    "incoterms": "FOB",
    "thickness_mm": 20,
}


class TestIndustryProfileInjection:
    def test_default_behavior_unchanged(self):
        """未传 profile → 内置建材默认（零漂移基线）。"""
        calc = BOQCalculator().calculate(dict(BASE_PARAMS))
        assert calc["base_price"] == 25.0  # ceramic 默认基价
        assert calc["total"] > 0

    def test_profile_overrides_base_price(self):
        """机械行业包：ceramic 键不存在于基价表 → 走覆盖值（验证注入生效）。"""
        profile = {
            "material_base_prices": {"ceramic": 55.0},
            "grade_multipliers": {"standard": 1.0},
        }
        calc = BOQCalculator().calculate(dict(BASE_PARAMS), industry_profile=profile)
        assert calc["base_price"] == 55.0
        assert calc["total"] > calc.get("base_price", 0)

    def test_density_override_changes_containers(self):
        """密度覆盖影响配载估算（轻质材料 → 更少 20GP 柜）。"""
        heavy = BOQCalculator().calculate(
            dict(BASE_PARAMS), industry_profile={"material_densities": {"ceramic": 5000}}
        )
        light = BOQCalculator().calculate(
            dict(BASE_PARAMS), industry_profile={"material_densities": {"ceramic": 500}}
        )
        h_cont = heavy["breakdown"]["estimated_20gp_containers"]
        l_cont = light["breakdown"]["estimated_20gp_containers"]
        assert h_cont > l_cont

    def test_moq_tier_override(self):
        """MOQ 折扣档可由 Profile 覆盖：同数量下覆盖档给出**更高**折扣 → 注入真的生效。

        基线（建材默认档）：quantity_sqm=1000 命中 {1000, 5%} → total = 25000 * 0.95 = 23750。
        覆盖档 {500, 12%}：同数量命中 12% → total = 25000 * 0.88 = 22000。
        旧构造（覆盖档折扣率同为 5%）两边恒等，无法区分注入是否生效，故不可用。
        """
        profile = {"moq_tiers": [{"min_quantity_sqm": 500, "discount_rate": 0.12}]}
        with_discount = BOQCalculator().calculate(
            dict(BASE_PARAMS), industry_profile=profile
        )
        without = BOQCalculator().calculate(dict(BASE_PARAMS))
        assert without["total"] == 23750.0  # 建材默认 5% 档
        assert with_discount["total"] == 22000.0  # 覆盖 12% 档
        assert with_discount["total"] < without["total"]
