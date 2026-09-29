# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""第二层补充缺口 E · 成本与毛利服务（Unit Economics & Margin Service）。

负责直接成本事件入库与租户单位经济核算：
Revenue - Direct Cost = Gross Margin。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cost_event import CostEvent
from app.models.finance_ledger import FinanceLedgerEntry, ENTRY_TYPE_REVENUE

logger = logging.getLogger("uj-admin.services.cost_service")



def record_cost_event(
    db: Session,
    *,
    tenant_id: Optional[str],
    cost_code: str,
    cost_category: str,
    amount: float,
    currency: str = "USD",
    quantity: float = 1.0,
    unit: str = "unit",
    subject_type: Optional[str] = None,
    subject_id: Optional[str] = None,
    provider: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> CostEvent:
    """写入一条成本事件（append-only 留痕）。"""
    event = CostEvent(
        tenant_id=tenant_id,
        cost_code=cost_code,
        cost_category=cost_category,
        amount=round(float(amount), 4),
        currency=currency,
        quantity=float(quantity),
        unit=unit,
        subject_type=subject_type,
        subject_id=subject_id,
        provider=provider,
        meta_json=meta or {},
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info(
        "Cost event recorded: tenant=%s code=%s amount=%s%s",
        tenant_id, cost_code, amount, currency,
    )
    return event


def get_tenant_unit_economics(
    db: Session,
    *,
    tenant_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> dict[str, Any]:
    """计算租户在指定时间窗口的单位经济模型与毛利：

    - Revenue: 财务账本 (finance_ledger_entries) 中的正向营收
    - Direct Cost: 成本事件 (cost_events) 中的各项消耗
    - Gross Margin: Revenue - Direct Cost
    - Gross Margin Rate: (Revenue - Direct Cost) / Revenue
    """
    # 1. 营收统计
    rev_q = db.query(func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0)).filter(
        FinanceLedgerEntry.tenant_id == tenant_id,
        FinanceLedgerEntry.entry_type.in_(ENTRY_TYPE_REVENUE),
    )
    if start_time:
        rev_q = rev_q.filter(FinanceLedgerEntry.created_at >= start_time)
    if end_time:
        rev_q = rev_q.filter(FinanceLedgerEntry.created_at <= end_time)
    total_revenue = round(float(rev_q.scalar() or 0) / 100.0, 4)


    # 2. 成本统计（按 category 分组）
    cost_q = db.query(
        CostEvent.cost_category,
        func.coalesce(func.sum(CostEvent.amount), 0.0).label("subtotal"),
    ).filter(CostEvent.tenant_id == tenant_id)
    if start_time:
        cost_q = cost_q.filter(CostEvent.occurred_at >= start_time)
    if end_time:
        cost_q = cost_q.filter(CostEvent.occurred_at <= end_time)
    cost_rows = cost_q.group_by(CostEvent.cost_category).all()

    cost_breakdown: dict[str, float] = {}
    total_cost = 0.0
    for cat, sub in cost_rows:
        val = float(sub)
        cost_breakdown[cat] = round(val, 4)
        total_cost += val

    gross_margin = round(total_revenue - total_cost, 4)
    margin_rate = round(gross_margin / total_revenue, 4) if total_revenue > 0 else 0.0

    return {
        "tenant_id": tenant_id,
        "revenue": round(total_revenue, 4),
        "direct_cost": round(total_cost, 4),
        "gross_margin": gross_margin,
        "gross_margin_rate": margin_rate,
        "cost_breakdown": cost_breakdown,
        "is_profitable": gross_margin >= 0.0,
    }
