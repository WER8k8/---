"""状态枚举定义 —— ORCH-08/09/10 修复

统一订单、支付、商机等核心实体的状态词汇，避免多套互斥词汇并存。
"""

from __future__ import annotations

import enum
from typing import FrozenSet


class OrderStatus(str, enum.Enum):
    """订单状态机 —— ORCH-08/09 统一词汇"""
    DRAFT = "draft"             # 草稿
    PENDING = "pending"         # 待支付
    PAID = "paid"               # 已支付
    CONFIRMED = "confirmed"     # 已确认
    SHIPPED = "shipped"         # 已发货
    COMPLETED = "completed"     # 已完成
    CANCELLED = "cancelled"     # 已取消
    REFUNDED = "refunded"       # 已退款
    PARTIAL_REFUNDED = "partial_refunded"  # 部分退款
    # 有效跃迁白名单
    _TRANSITIONS: FrozenSet[frozenset] = frozenset({
        frozenset({DRAFT, PENDING}),           # 草稿 → 待支付
        frozenset({PENDING, PAID}),            # 待支付 → 已支付
        frozenset({PAID, CONFIRMED}),          # 已支付 → 已确认
        frozenset({CONFIRMED, SHIPPED}),       # 已确认 → 已发货
        frozenset({SHIPPED, COMPLETED}),       # 已发货 → 已完成
        frozenset({DRAFT, CANCELLED}),         # 草稿 → 已取消
        frozenset({PENDING, CANCELLED}),       # 待支付 → 已取消
        frozenset({PAID, REFUNDED}),           # 已支付 → 已退款
        frozenset({PAID, PARTIAL_REFUNDED}),   # 已支付 → 部分退款
    })
    @classmethod
    def is_valid_transition(cls, from_status: str, to_status: str) -> bool:
        """校验状态跃迁是否合法"""
        try:
            src = cls(from_status)
            dst = cls(to_status)
        except ValueError:
            return False
        return frozenset({src, dst}) in cls._TRANSITIONS

    @classmethod
    def valid_next_statuses(cls, current: str) -> list[str]:
        """返回当前状态的所有合法下一状态"""
        try:
            src = cls(current)
        except ValueError:
            return []
        nexts = set()
        for transition in cls._TRANSITIONS:
            if src in transition:
                other = (transition - {src}).pop()
                nexts.add(other.value)
        return sorted(nexts)


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
