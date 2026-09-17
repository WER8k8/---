# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""状态枚举定义 —— ORCH-08/09/10 修复

统一订单、支付、商机等核心实体的状态词汇，避免多套互斥词汇并存。
"""

from __future__ import annotations

import enum
from typing import FrozenSet


# 订单状态跃迁集合（模块级常量，避免被 str 枚举误当成员注册；元组有序，限制为有向跃迁）
_ORDER_TRANSITIONS: FrozenSet[tuple[str, str]] = frozenset({
    ("draft", "pending"),           # 草稿 → 待支付
    ("pending", "paid"),            # 待支付 → 已支付
    ("pending", "deposit_received"), # 待支付 → 定金已收（首付30%直接核销）
    ("paid", "confirmed"),          # 已支付 → 已确认
    ("confirmed", "deposit_received"),  # 已确认 → 定金已收（④定金核销）
    ("deposit_received", "in_production"),  # 定金已收 → 生产中（⑤生产跟单）
    ("confirmed", "in_production"), # 已确认 → 生产中（跳过定金，兼容预付款/信用客户）
    ("in_production", "shipped"),   # 生产中 → 已发货
    ("confirmed", "shipped"),       # 已确认 → 已发货（可直发，不强制生产阶段）
    ("shipped", "final_payment_received"),  # 已发货 → 尾款已收（⑦尾款核销）
    ("final_payment_received", "completed"),  # 尾款已收 → 已完成
    ("shipped", "completed"),       # 已发货 → 已完成（跳过尾款，兼容全款预付）
    ("draft", "cancelled"),         # 草稿 → 已取消
    ("pending", "cancelled"),       # 待支付 → 已取消
    ("paid", "refunded"),           # 已支付 → 已退款
    ("paid", "partial_refunded"),   # 已支付 → 部分退款
})


class OrderStatus(str, enum.Enum):
    """订单状态机 —— ORCH-08/09 统一词汇"""
    DRAFT = "draft"             # 草稿
    PENDING = "pending"         # 待支付
    PAID = "paid"               # 已支付
    CONFIRMED = "confirmed"     # 已确认
    DEPOSIT_RECEIVED = "deposit_received"  # 定金已收（④定金核销）
    IN_PRODUCTION = "in_production"  # 生产中（⑤生产跟单）
    SHIPPED = "shipped"         # 已发货
    FINAL_PAYMENT_RECEIVED = "final_payment_received"  # 尾款已收（⑦尾款核销）
    COMPLETED = "completed"     # 已完成
    CANCELLED = "cancelled"     # 已取消
    REFUNDED = "refunded"       # 已退款
    PARTIAL_REFUNDED = "partial_refunded"  # 部分退款

    @classmethod
    def is_valid_transition(cls, from_status: str, to_status: str) -> bool:
        """校验状态跃迁是否合法（有向）"""
        return (from_status, to_status) in _ORDER_TRANSITIONS

    @classmethod
    def valid_next_statuses(cls, current: str) -> list[str]:
        """返回当前状态的所有合法下一状态"""
        return sorted(to for fr, to in _ORDER_TRANSITIONS if fr == current)


class PaymentStatus(str, enum.Enum):
    """支付状态机 —— ORCH-09 统一词汇"""
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class OpportunityStage(str, enum.Enum):
    """商机阶段机 —— ORCH-10 统一词汇"""
    PROSPECTING = "prospecting"      #  prospecting
    QUALIFICATION = "qualification"  # 资格确认
    NEEDS_ANALYSIS = "needs_analysis"  # 需求分析
    PROPOSAL = "proposal"           # 方案报价
    NEGOTIATION = "negotiation"     # 谈判
    WON = "won"                     # 赢单
    LOST = "lost"                   # 输单
    @classmethod
    def valid_next_statuses(cls, current: str) -> list[str]:
        """返回当前阶段的所有合法下一阶段"""
        order = [e.value for e in cls]
        try:
            idx = order.index(current)
        except ValueError:
            return []
        # 只能向后推进或结束
        return order[idx + 1:] if idx < len(order) - 1 else []


class LeadStatus(str, enum.Enum):
    """线索状态机 —— ORCH-10 统一词汇"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NURTUREING = "nurtureing"
    CONVERTED = "converted"
    DISCARDED = "discarded"


# 状态白名单常量（供路由层快速校验）
VALID_ORDER_STATUSES: FrozenSet[str] = frozenset(e.value for e in OrderStatus)
VALID_PAYMENT_STATUSES: FrozenSet[str] = frozenset(e.value for e in PaymentStatus)
VALID_OPPORTUNITY_STAGES: FrozenSet[str] = frozenset(e.value for e in OpportunityStage)
VALID_LEAD_STATUSES: FrozenSet[str] = frozenset(e.value for e in LeadStatus)


def validate_status(value: str, allowed: FrozenSet[str], entity: str = "状态") -> tuple[bool, str]:
    """通用状态校验工具函数"""
    if value not in allowed:
        return False, f"无效的{entity} '{value}'，允许值: {', '.join(sorted(allowed))}"
    return True, ""
