# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""代理业绩看板 — 聚合租户、支付、财务台账与分润结算。"""

from __future__ import annotations

import json
import logging
import re
import uuid
from calendar import monthrange
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.commission_settlement import AgentCommissionSettlement
from app.models.finance_ledger import FinanceLedgerEntry
from app.models.payment import PaymentOrder
from app.models.tenant import Tenant, TenantPlan
from app.models.user import User
from app.core.no_fake_delivery import is_production_environment, mock_allowed
from app.services.agent_aggregation_service import AgentAggregationService

_AGENT_PORTAL_MOCK_TREND_FLAG = "AGENT_PORTAL_MOCK_TREND"

STATUS_LABELS = {
    "trial": "试用中",
    "active": "已付费",
    "suspended": "已冻结",
    "cancelled": "已到期",
}

PLAN_LABELS = {
    "free": "免费版",
    "basic": "基础版",
    "standard": "标准版",
    "pro": "高级版",
    "enterprise": "企业版",
    "flagship": "旗舰版",
}


def _parse_settings(raw: Any) -> dict:
    """_parse_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def _month_start(dt: datetime) -> datetime:
    """_month_start。

    参数说明：
    :param dt: 参数 dt
    :return: 返回处理结果。
    """
    return datetime(dt.year, dt.month, 1, tzinfo=timezone.utc)


def _month_end(dt: datetime) -> datetime:
    """_month_end。

    参数说明：
    :param dt: 参数 dt
    :return: 返回处理结果。
    """
    last = monthrange(dt.year, dt.month)[1]
    return datetime(dt.year, dt.month, last, 23, 59, 59, tzinfo=timezone.utc)


def _format_yuan(cents: int | float) -> str:
    """_format_yuan。

    参数说明：
    :param cents: 参数 cents
    :return: 返回处理结果。
    """
    return f"{int(cents) / 100:,.2f}"


class AgentPortalService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def resolve_node_id(self, user: User) -> str:
        """优先 DB 中 agent_user_id 绑定，否则按角色 Mock 映射。"""
        try:
            from app.models.agent_tree import AgentNode
            row = (
                self.db.query(AgentNode.id)
                .filter(AgentNode.agent_user_id == user.id, AgentNode.is_active.is_(True))
                .first()
            )
            if row:
                return str(row[0])
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("查询 AgentNode 失败: %s", e)
            pass
        return AgentAggregationService.get_user_node_id(user.role, self.db)

    def _subtree_node_ids(self, node_id: str) -> set[str]:
        """_subtree_node_ids。

        参数说明：
        :param self: 参数 self
        :param node_id: 参数 node_id
        :return: 返回处理结果。
        """
        return AgentAggregationService.collect_subtree_node_ids(self.db, node_id)

    def _tenant_scope_query(self, user: User, node_id: str):
        """_tenant_scope_query。

        参数说明：
        :param self: 参数 self
        :param user: 参数 user
        :param node_id: 参数 node_id
        :return: 返回处理结果。
        """
        q = self.db.query(Tenant)
        if user.role in ("admin", "super_admin"):
            return q
        subtree = self._subtree_node_ids(node_id)
        tenants = q.all()
        scoped_ids: list[str] = []
        for t in tenants:
            settings = _parse_settings(t.settings)
            agent_nid = settings.get("agent_node_id")
            opened_by = settings.get("opened_by_agent_user_id")
            if agent_nid and str(agent_nid) in subtree:
                scoped_ids.append(str(t.id))
            elif opened_by and str(opened_by) == str(user.id):
                scoped_ids.append(str(t.id))
        if not scoped_ids:
            return q.filter(Tenant.id.in_([]))
        return q.filter(Tenant.id.in_(scoped_ids))

    def _tenant_ids(self, user: User, node_id: str) -> list[str]:
        """_tenant_ids。

        参数说明：
        :param self: 参数 self
        :param user: 参数 user
        :param node_id: 参数 node_id
        :return: 返回处理结果。
        """
        return [str(t.id) for t in self._tenant_scope_query(user, node_id).all()]

    def _pending_commission_cents(self, node_id: str) -> int:
        """_pending_commission_cents。

        参数说明：
        :param self: 参数 self
        :param node_id: 参数 node_id
        :return: 返回处理结果。
        """
        total = (
            self.db.query(func.coalesce(func.sum(AgentCommissionSettlement.commission_cents), 0))
            .filter(
                AgentCommissionSettlement.agent_node_id == node_id,
                AgentCommissionSettlement.status == "pending",
            )
            .scalar()
        )
        return int(total or 0)

    def build_dashboard(self, user: User) -> dict[str, Any]:
        """build_dashboard。

        参数说明：
        :param self: 参数 self
        :param user: 参数 user
        :return: 返回处理结果。
        """
        node_id = self.resolve_node_id(user)
        mock = AgentAggregationService.get_subtree_stats(self.db, node_id)
        if not mock:
            return {}

        tenant_ids = self._tenant_ids(user, node_id)
        now = datetime.now(timezone.utc)
        month_start = _month_start(now)
        total_clients = len(tenant_ids)
        monthly_new = 0
        monthly_revenue_cents = 0
        if tenant_ids:
            monthly_new = (
                self.db.query(func.count(Tenant.id))
                .filter(Tenant.id.in_(tenant_ids), Tenant.created_at >= month_start)
                .scalar()
            ) or 0
            monthly_revenue_cents = int(
                self.db.query(func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0))
                .filter(
                    FinanceLedgerEntry.tenant_id.in_(tenant_ids),
                    FinanceLedgerEntry.entry_type == "revenue",
                    FinanceLedgerEntry.recorded_at >= month_start,
                )
                .scalar()
                or 0
            )

        monthly_revenue_count = 0
        if tenant_ids:
            monthly_revenue_count = (
                self.db.query(func.count(PaymentOrder.id))
                .filter(
                    PaymentOrder.tenant_id.in_(tenant_ids),
                    PaymentOrder.status == "paid",
                    PaymentOrder.paid_at >= month_start,
                )
                .scalar()
            ) or 0

        pending_commission = self._pending_commission_cents(node_id)
        pending_commission_cents = pending_commission
        use_db = total_clients > 0 or monthly_revenue_cents > 0
        if use_db:
            stats = {
                "total_clients": total_clients,
                "monthly_new_clients": int(monthly_new),
                "monthly_revenue": monthly_revenue_cents / 100.0,
                "monthly_revenue_cents": monthly_revenue_cents,
                "monthly_revenue_count": int(monthly_revenue_count),
                "pending_commission": pending_commission / 100.0,
                "pending_commission_cents": pending_commission_cents,
                "estimated_settle_date": self._next_settle_date(),
                "data_source": "db",
            }
        else:
            stats = {
                "total_clients": 0,
                "monthly_new_clients": 0,
                "monthly_revenue": 0.0,
                "monthly_revenue_cents": 0,
                "monthly_revenue_count": 0,
                "pending_commission": pending_commission / 100.0,
                "pending_commission_cents": pending_commission_cents,
                "estimated_settle_date": self._next_settle_date(),
                "data_source": "empty",
            }

        children = AgentAggregationService.get_children(node_id, self.db) or []
        subordinates = [
            {
                "node_id": c["id"],
                "name": c["name"],
                "level": c["level"],
                "level_label": {"l2": "省代", "l3": "区域", "l4": "市级", "l5": "街道"}.get(c["level"], c["level"]),
                "client_count": c.get("stats", {}).get("total_clients", 0),
                "revenue": _format_yuan(int((c.get("stats", {}).get("monthly_revenue") or 0) * 100)),
                "monthly_new": c.get("stats", {}).get("new_clients_this_month", 0),
            }
            for c in children
        ]
        return {
            "node": mock.get("node"),
            "stats": stats,
            "subordinates": subordinates,
            "by_level": mock.get("by_level") or [],
            "forbidden_admin_paths": True,
        }

    def list_clients(
        self,
        user: User,
        *,
        search: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """list_clients。

        参数说明：
        :param self: 参数 self
        :param user: 参数 user
        :param search: 参数 search
        :param status: 参数 status
        :param page: 参数 page
        :param page_size: 参数 page_size
        :return: 返回处理结果。
        """
        node_id = self.resolve_node_id(user)
        q = self._tenant_scope_query(user, node_id)
        if search:
            q = q.filter(Tenant.name.ilike(f"%{search}%"))
        if status:
            rev = {v: k for k, v in STATUS_LABELS.items()}
            code = rev.get(status, status)
            q = q.filter(Tenant.status == code)
        total = q.count()
        rows = (
            q.order_by(Tenant.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        items = []
        # 批量查询所有租户的首笔付款，避免 N+1
        first_payments = {}
        if rows:
            row_ids = [str(t.id) for t in rows]
            payment_rows = (
                self.db.query(
                    PaymentOrder.tenant_id,
                    func.coalesce(func.min(PaymentOrder.created_at), func.now()),
                )
                .filter(
                    PaymentOrder.tenant_id.in_(row_ids),
                    PaymentOrder.status == "paid",
                )
                .group_by(PaymentOrder.tenant_id)
                .all()
            )
            first_payments = {str(r[0]): int(r[1] or 0) for r in payment_rows}

        for t in rows:
            plan_label = PLAN_LABELS.get(t.plan.code if t.plan else "", t.plan.name if t.plan else "—")
            first_pay = first_payments.get(str(t.id), 0)
            items.append(
                {
                    "id": str(t.id),
                    "name": t.name,
                    "package": plan_label,
                    "open_date": t.created_at.date().isoformat() if t.created_at else "",
                    "first_payment": f"¥{_format_yuan(int(first_pay or 0))}",
                    "status": STATUS_LABELS.get(t.status, t.status),
                }
            )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def list_payments(
        self,
        user: User,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """list_payments。

        参数说明：
        :param self: 参数 self
        :param user: 参数 user
        :param page: 参数 page
        :param page_size: 参数 page_size
        :return: 返回处理结果。
        """
        node_id = self.resolve_node_id(user)
        tenant_ids = self._tenant_ids(user, node_id)
        if not tenant_ids:
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

        q = self.db.query(PaymentOrder).filter(
            PaymentOrder.tenant_id.in_(tenant_ids),
            PaymentOrder.status == "paid",
        ).options(joinedload(PaymentOrder.tenant).joinedload(Tenant.plan))
        total = q.count()
        orders = (
            q.order_by(PaymentOrder.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        channel_labels = {"wechat": "微信支付", "alipay": "支付宝", "stripe": "Stripe", "bank": "银行转账"}
        items = []
        for o in orders:
            tenant_name = o.tenant.name if o.tenant else "—"
            plan_label = PLAN_LABELS.get(o.tenant.plan.code if o.tenant and o.tenant.plan else "", "—")
            items.append(
                {
                    "id": str(o.id),
                    "client_name": tenant_name,
                    "package": plan_label,
                    "amount": f"¥{_format_yuan(o.amount)}",
                    "pay_time": (o.paid_at or o.created_at).strftime("%Y-%m-%d %H:%M") if (o.paid_at or o.created_at) else "",
                    "method": channel_labels.get(o.channel, o.channel),
                    "status": "已到账",
                }
            )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def monthly_trends(self, user: User, months: int = 6) -> dict[str, Any]:
        """monthly_trends。

        参数说明：
        :param self: 参数 self
        :param user: 参数 user
        :param months: 参数 months
        :return: 返回处理结果。
        """
        node_id = self.resolve_node_id(user)
        tenant_ids = self._tenant_ids(user, node_id)
        now = datetime.now(timezone.utc)
        trends: list[dict[str, Any]] = []
        for i in range(months - 1, -1, -1):
            y = now.year
            m = now.month - i
            while m <= 0:
                m += 12
                y -= 1
            start = datetime(y, m, 1, tzinfo=timezone.utc)
            end = _month_end(start)
            label = f"{y}-{m:02d}"
            clients = 0
            revenue_cents = 0
            if tenant_ids:
                clients = (
                    self.db.query(func.count(Tenant.id))
                    .filter(Tenant.id.in_(tenant_ids), Tenant.created_at >= start, Tenant.created_at <= end)
                    .scalar()
                ) or 0
                revenue_cents = int(
                    self.db.query(func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0))
                    .filter(
                        FinanceLedgerEntry.tenant_id.in_(tenant_ids),
                        FinanceLedgerEntry.entry_type == "revenue",
                        FinanceLedgerEntry.recorded_at >= start,
                        FinanceLedgerEntry.recorded_at <= end,
                    )
                    .scalar()
                    or 0
                )

            if not tenant_ids:
                trends.append({"month": label, "clients": 0, "revenue": 0.0})
                continue

            trends.append({"month": label, "clients": int(clients), "revenue": revenue_cents / 100.0})

        return {"items": trends, "months": months}

    @staticmethod
    def _next_settle_date() -> str:
        """_next_settle_date。
        :return: 返回处理结果。
        """
        now = datetime.now(timezone.utc)
        y, m = now.year, now.month
        if now.day >= 15:
            m += 1
            if m > 12:
                m = 1
                y += 1
        return f"{y}-{m:02d}-15"

    def create_account_opening(self, user: User, payload: dict[str, Any]) -> dict[str, Any]:
        """代理提交开户申请 — 创建 trial 租户并绑定代理节点。"""
        node_id = self.resolve_node_id(user)
        company = (payload.get("company_name") or payload.get("companyName") or "").strip()
        contact = (payload.get("contact_name") or payload.get("contactName") or "").strip()
        phone = (payload.get("phone") or "").strip()
        email = (payload.get("email") or "").strip()
        package_code = (payload.get("package") or "basic").strip().lower()
        if not company or not contact or not phone:
            raise ValueError("公司名称、联系人、联系电话为必填")

        plan = (
            self.db.query(TenantPlan)
            .filter(TenantPlan.code == package_code, TenantPlan.is_active.is_(True))
            .first()
        )
        if not plan:
            plan = self.db.query(TenantPlan).filter(TenantPlan.is_active.is_(True)).first()
        if not plan:
            raise ValueError("未配置可用套餐，请联系超管")

        slug = re.sub(r"[^a-z0-9]+", "-", company.lower())[:20] or "client"
        domain = f"{slug}-{uuid.uuid4().hex[:6]}.youding.local"
        chain = AgentAggregationService.get_chain_up_any(node_id, self.db) or []
        settings = json.dumps(
            {
                "agent_node_id": node_id,
                "agent_chain": chain,
                "opened_by_agent_user_id": str(user.id),
                "opening_remark": (payload.get("remark") or "")[:500],
                "package_code": package_code,
            },
            ensure_ascii=False,
        )
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=company,
            contact_name=contact,
            contact_phone=phone,
            contact_email=email or None,
            domain=domain,
            plan_id=plan.id,
            status="trial",
            is_active=True,
            settings=settings,
        )
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return {
            "tenant_id": str(tenant.id),
            "name": tenant.name,
            "domain": tenant.domain,
            "status": STATUS_LABELS.get(tenant.status, tenant.status),
            "plan": plan.name,
            "plan_id": str(plan.id),
            "package_code": package_code,
            "agent_node_id": node_id,
            "agent_chain": chain,
        }

    def assert_tenant_in_scope(self, user: User, tenant_id: str) -> Tenant:
        """代理只能对自己辖区租户收款。"""
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError("租户不存在")
        if user.role in ("admin", "super_admin"):
            return tenant
        scoped = self._tenant_ids(user, self.resolve_node_id(user))
        if str(tenant.id) not in scoped:
            raise ValueError("无权对该客户发起收款")
        return tenant
