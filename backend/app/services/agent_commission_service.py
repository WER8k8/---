# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""支付成功 → 多级代理分润（沿 agent-tree 向上拆分，幂等）。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.commission_settlement import AgentCommissionSettlement
from app.models.payment import PaymentOrder
from app.models.tenant import Tenant
from app.services.agent_aggregation_service import AgentAggregationService
from app.services.commission_rule_service import CommissionRuleService

# 兼容旧单级逻辑（规则表不可用时）
FIRST_PAYMENT_RATE_BP = 3000
RENEWAL_RATE_BP = 1000
PLATFORM_LEVEL = "l1"


def _parse_settings(raw: Any) -> dict:
    """_parse_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        return json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def _tenant_agent_node_id(tenant: Tenant) -> Optional[str]:
    """_tenant_agent_node_id。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    node_id = _parse_settings(tenant.settings).get("agent_node_id")
    return str(node_id) if node_id else None


def _tenant_agent_chain(db: Session, tenant: Tenant) -> list[dict[str, Any]]:
    """_tenant_agent_chain。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    settings = _parse_settings(tenant.settings)
    chain = settings.get("agent_chain")
    if isinstance(chain, list) and chain:
        return chain
    node_id = settings.get("agent_node_id")
    if not node_id:
        return []
    built = AgentAggregationService.get_chain_up_any(str(node_id), db)
    return built or []


def _order_ref(order: PaymentOrder) -> str:
    """_order_ref。

    参数说明：
    :param order: 参数 order
    :return: 返回处理结果。
    """
    return f"payment_order:{order.id}"


def _payment_kind(db: Session, order: PaymentOrder, tenant_id: str) -> str:
    """_payment_kind。

    参数说明：
    :param db: 参数 db
    :param order: 参数 order
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    prior_paid = (
        db.query(PaymentOrder)
        .filter(
            PaymentOrder.tenant_id == tenant_id,
            PaymentOrder.status == "paid",
            PaymentOrder.id != order.id,
        )
        .count()
    )
    return "first" if prior_paid == 0 else "renewal"


def _settlement_exists(db: Session, agent_node_id: str, ref_tag: str) -> bool:
    """_settlement_exists。

    参数说明：
    :param db: 参数 db
    :param agent_node_id: 参数 agent_node_id
    :param ref_tag: 参数 ref_tag
    :return: 返回处理结果。
    """
    return (
        db.query(AgentCommissionSettlement.id)
        .filter(
            AgentCommissionSettlement.agent_node_id == agent_node_id,
            AgentCommissionSettlement.note.contains(ref_tag),
        )
        .first()
        is not None
    )


def accrue_commission_for_payment(db: Session, order: PaymentOrder) -> Optional[dict[str, Any]]:
    """支付入账后按规则表向代理链各级计提待结算分润。"""
    if order.status != "paid" or not order.amount:
        return None

    tenant = db.query(Tenant).filter(Tenant.id == order.tenant_id).first()
    if not tenant:
        return None

    chain = _tenant_agent_chain(db, tenant)
    if not chain:
        node_id = _tenant_agent_node_id(tenant)
        if not node_id:
            return None
        chain = [{"id": node_id, "level": "l3", "name": node_id}]

    ref_tag = _order_ref(order)
    kind = _payment_kind(db, order, str(tenant.id))
    rules = CommissionRuleService(db).rules_map()
    paid_at = order.paid_at or order.created_at or datetime.now(timezone.utc)
    period = paid_at.strftime("%Y-%m")
    kind_label = "首次付款" if kind == "first" else "续费"
    created: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for hop in chain:
        level = hop.get("level") or ""
        node_id = str(hop.get("id") or "")
        if not node_id or level == PLATFORM_LEVEL:
            continue

        rate_bp = rules.get((kind, level))
        if rate_bp is None and not rules:
            rate_bp = FIRST_PAYMENT_RATE_BP if kind == "first" else RENEWAL_RATE_BP
            if len(chain) > 1:
                rate_bp = 0
            if hop != chain[-1]:
                rate_bp = 0
        if not rate_bp or rate_bp <= 0:
            continue

        if _settlement_exists(db, node_id, ref_tag):
            skipped.append({"agent_node_id": node_id, "level": level})
            continue

        commission_cents = order.amount * rate_bp // 10000
        if commission_cents <= 0:
            continue

        row = AgentCommissionSettlement(
            agent_node_id=node_id,
            period=period,
            revenue_cents=order.amount,
            commission_cents=commission_cents,
            commission_rate_bp=rate_bp,
            status="pending",
            note=(
                f"{ref_tag}; tenant={tenant.id}; {kind_label}; "
                f"level={level}; order_no={order.order_no}"
            ),
        )
        db.add(row)
        db.flush()
        created.append(
            {
                "settlement_id": str(row.id),
                "agent_node_id": node_id,
                "agent_level": level,
                "commission_cents": commission_cents,
                "commission_rate_bp": rate_bp,
            }
        )

    if not created and not skipped:
        return None

    return {
        "payment_kind": kind,
        "period": period,
        "chain_levels": [h.get("level") for h in chain],
        "created": created,
        "skipped": skipped,
        "total_commission_cents": sum(c["commission_cents"] for c in created),
    }
