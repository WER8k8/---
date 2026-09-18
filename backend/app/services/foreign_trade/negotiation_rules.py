# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""阶梯让步配置引擎 —— 将 round_1/round_2/round_3 硬编码逻辑抽成可配置规则。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, ClassVar


# ── 结果数据结构 ──────────────────────────────────────────────
@dataclass
class ConcessionResult:
    """单次让步决策结果。"""
    concession_price: float
    concession_rate: float
    needs_approval: bool
    reason: str


# ── 规则配置 ──────────────────────────────────────────────────
@dataclass
class NegotiationRules:
    """多轮次议价让步规则配置。"""

    # 每轮最大允许自动折扣百分比（key = round_no, value = max_discount_pct）
    round_discounts: Dict[int, float] = field(
        default_factory=lambda: {
            1: 0.0,   # 首轮不轻易打折
            2: 5.0,   # 第二轮最多让 5%
            3: 10.0,  # 第三轮最多让 10%
            4: 15.0,
            5: 20.0,
        }
    )

    # 底价利润率（成本 * (1 + floor_margin_pct/100) 为底价）
    floor_margin_pct: float = 8.0

    # 全自动议价授权上限（超出须走审批流）
    max_auto_discount_pct: float = 5.0

    # MOQ 联动折扣表：[(min_qty, discount_pct), ...]，按 min_qty 降序匹配第一条
    moq_discount_table: List[Dict[str, Any]] = field(
        default_factory=lambda: [
            {"min_qty": 1000, "discount_pct": 3.0},
            {"min_qty": 500, "discount_pct": 2.0},
            {"min_qty": 100, "discount_pct": 1.0},
        ]
    )

    # 是否启用底价红线保护（低于底价必须审批）
    enforce_floor_price: bool = True

    # 默认实例（与原有硬编码行为保持完全一致）。
    # 声明为 ClassVar，避免被 dataclass 当作字段处理。
    DEFAULT: ClassVar[Optional["NegotiationRules"]] = None

    def apply_concession(
        self,
        *,
        round_no: int,
        requested_discount: float,
        base_price: float,
        base_cost: float,
        quantity: float = 1.0,
    ) -> ConcessionResult:
        """计算本轮让步决策。

        参数说明：
            round_no: 当前谈判轮次（从 1 开始）
            requested_discount: 买家请求的折扣百分比
            base_price: 当前报价单价
            base_cost: 产品成本单价
            quantity: 订单数量（用于 MOQ 联动）

        返回：
            ConcessionResult：让步后的价格、实际折扣率、是否需要审批、原因说明
        """
        # 计算底价红线
        floor_price = base_cost * (1.0 + self.floor_margin_pct / 100.0) if base_cost > 0 else 0.0

        # 获取本轮允许的最大自动折扣
        allowed_discount = self.round_discounts.get(round_no, self.max_auto_discount_pct)

        # MOQ 联动：与买家请求折扣取更优（对买家更有利），不叠加双计
        # （「取更有利的」= max；若相加会把 4% 请求打成 7% 误触审批，与 Round-2 授权 5% 口径冲突）
        moq_bonus = 0.0
        for entry in sorted(self.moq_discount_table, key=lambda e: e["min_qty"], reverse=True):
            if quantity >= float(entry["min_qty"]):
                moq_bonus = float(entry.get("discount_pct", 0.0))
                break

        effective_requested = max(float(requested_discount or 0.0), moq_bonus)

        # 决策逻辑（与原有 hardcode 行为对齐）
        if round_no == 1:
            # 首轮坚挺：不轻易打折
            final_rate = 0.0
            final_price = base_price
            needs_approval = False
            reason = "首轮议价：坚持标准报价，强调品质与交付能力"
        elif effective_requested <= allowed_discount and effective_requested <= self.max_auto_discount_pct:
            # 在授权范围内让步
            final_rate = min(effective_requested, allowed_discount)
            final_price = round(base_price * (1.0 - final_rate / 100.0), 2)
            # 底价保护
            if self.enforce_floor_price and floor_price > 0 and final_price < floor_price:
                final_price = floor_price
                final_rate = round((1.0 - final_price / base_price) * 100, 2)
                needs_approval = False
                reason = f"底价红线保护：让利后价格 {final_price:.2f} 不低于成本底线 {floor_price:.2f}"
            else:
                needs_approval = False
                reason = f"自动授权内让步：折扣 {final_rate:.1f}% 在 Round-{round_no} 授权范围内"
        else:
            # 超出授权：触发审批
            needs_approval = True
            target_price = round(base_price * (1.0 - effective_requested / 100.0), 2)
            # 如果低于底价则追加底价说明
            if self.enforce_floor_price and floor_price > 0 and target_price < floor_price:
                reason = (
                    f"深度折扣超出授权阈值：请求 {effective_requested:.1f}% 折扣 "
                    f"对应价格 {target_price:.2f} 低于底价 {floor_price:.2f}，需主管审批"
                )
            else:
                reason = (
                    f"深度折扣超出自动授权：请求 {effective_requested:.1f}% 折扣，"
                    f"超过 Round-{round_no} 授权上限 {allowed_discount:.1f}%，需主管审批"
                )
            final_rate = effective_requested
            final_price = target_price

        return ConcessionResult(
            concession_price=final_price,
            concession_rate=final_rate,
            needs_approval=needs_approval,
            reason=reason,
        )


# ── 模块级便捷函数 ────────────────────────────────────────────
def apply_concession(
    *,
    rules: NegotiationRules,
    round_no: int,
    requested_discount: float,
    base_price: float,
    base_cost: float,
    quantity: float = 1.0,
) -> ConcessionResult:
    """模块级调用入口，避免每次显式传 rules 对象。"""
    return rules.apply_concession(
        round_no=round_no,
        requested_discount=requested_discount,
        base_price=base_price,
        base_cost=base_cost,
        quantity=quantity,
    )


# ── 默认实例 ──────────────────────────────────────────────────
# 类变量需要在类定义完成后赋值，使用 setattr 绕过
NegotiationRules.DEFAULT = NegotiationRules()
