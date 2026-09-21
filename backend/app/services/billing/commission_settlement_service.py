# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""代理商与区域合伙人分润结算服务 (Commission Settlement Service)。

支持七轨商业模式之【Lead Generation Commission 与渠道佣金】：
1. 市级代理商 (/agent/*)：成交金额的 3% (300 bps)
2. 区域代理商 (/partner)：成交金额的 2% (200 bps)
3. 订单达成 (Deal Won / Order Completed) 时自动触发佣金凭证生成
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CommissionSettlementService:
    """代理商与合伙人佣金结算核心服务。"""

    # 默认分润基准（万分比，1000 = 10%，300 = 3%，200 = 2%）
    DEFAULT_RATES_BP: Dict[str, int] = {
        "agent": 300,    # 市级代理 3%
        "partner": 200,  # 区域合伙人 2%
    }

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def settle_on_deal_won(
        self,
        *,
        order_id: str,
        deal_amount: float,
        currency: str = "USD",
        agent_node_id: Optional[str] = None,
        partner_node_id: Optional[str] = None,
        tenant_id: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """当大宗订单完成或赢单时，自动核算并生成代理与合伙人佣金单。"""
        amount_cents = int(round(deal_amount * 100))
        period_str = datetime.now(timezone.utc).strftime("%Y-%m")
        settlements: List[Dict[str, Any]] = []

        # 1. 市级代理佣金
        if agent_node_id:
            rate_bp = self.DEFAULT_RATES_BP["agent"]
            comm_cents = int(amount_cents * rate_bp / 10000)
            settlement_item = {
                "id": str(uuid.uuid4()),
                "role": "agent",
                "agent_node_id": agent_node_id,
                "period": period_str,
                "order_id": order_id,
                "revenue_cents": amount_cents,
                "commission_cents": comm_cents,
                "commission_amount": round(comm_cents / 100.0, 2),
                "commission_rate_bp": rate_bp,
                "commission_rate_pct": round(rate_bp / 100.0, 2),
                "currency": currency,
                "status": "pending",
                "note": note or f"市级代理订单 {order_id} 分润 (3%)",
            }
            settlements.append(settlement_item)
            self._persist_settlement(settlement_item)

        # 2. 区域合伙人佣金
        if partner_node_id:
            rate_bp = self.DEFAULT_RATES_BP["partner"]
            comm_cents = int(amount_cents * rate_bp / 10000)
            settlement_item = {
                "id": str(uuid.uuid4()),
                "role": "partner",
                "agent_node_id": partner_node_id,
                "period": period_str,
                "order_id": order_id,
                "revenue_cents": amount_cents,
                "commission_cents": comm_cents,
                "commission_amount": round(comm_cents / 100.0, 2),
                "commission_rate_bp": rate_bp,
                "commission_rate_pct": round(rate_bp / 100.0, 2),
                "currency": currency,
                "status": "pending",
                "note": note or f"区域合伙人订单 {order_id} 统筹分润 (2%)",
            }
            settlements.append(settlement_item)
            self._persist_settlement(settlement_item)

        total_commission = sum(s["commission_amount"] for s in settlements)

        return {
            "order_id": order_id,
            "deal_amount": round(deal_amount, 2),
            "currency": currency,
            "settlements_count": len(settlements),
            "settlements": settlements,
            "total_commission_amount": round(total_commission, 2),
            "period": period_str,
            "status": "settlements_generated",
        }

    def _persist_settlement(self, item: Dict[str, Any]) -> None:
        """持久化佣金结算单至数据库。"""
        if self.db is None:
            return
        try:
            from app.models.commission_settlement import AgentCommissionSettlement
            rec = AgentCommissionSettlement(
                id=item["id"],
                agent_node_id=item["agent_node_id"],
                period=item["period"],
                revenue_cents=item["revenue_cents"],
                commission_cents=item["commission_cents"],
                commission_rate_bp=item["commission_rate_bp"],
                status=item["status"],
                note=item.get("note"),
            )
            self.db.add(rec)
            self.db.commit()
        except Exception as exc:
            logger.warning("AgentCommissionSettlement 落库失败 (降级内存返回): %s", exc)
            try:
                self.db.rollback()
            except Exception:
                pass

    def get_agent_settlement_history(
        self,
        agent_node_id: str,
        period: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """查询代理商分润结算流水。"""
        if self.db is not None:
            try:
                from app.models.commission_settlement import AgentCommissionSettlement
                q = self.db.query(AgentCommissionSettlement).filter(
                    AgentCommissionSettlement.agent_node_id == agent_node_id
                )
                if period:
                    q = q.filter(AgentCommissionSettlement.period == period)
                rows = q.order_by(AgentCommissionSettlement.created_at.desc()).all()
                return [
                    {
                        "id": str(r.id),
                        "period": r.period,
                        "revenue_cents": r.revenue_cents,
                        "commission_cents": r.commission_cents,
                        "commission_amount": round(r.commission_cents / 100.0, 2),
                        "commission_rate_bp": r.commission_rate_bp,
                        "status": r.status,
                        "note": r.note,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    }
                    for r in rows
                ]
            except Exception:
                pass
        return []
