"""租户数据访问层"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.finance_ledger import FinanceLedgerEntry
from app.models.payment import PaymentOrder
from app.models.tenant import Tenant, TenantInvoice, TenantPlan, TenantSubscription
from app.repositories.base_repository import BaseRepository
from app.services.finance_honesty import (
    apply_real_paid_order_filters,
    revenue_ledger_conditions,
)


class TenantPlanRepository(BaseRepository[TenantPlan]):
    """套餐Repository"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        super().__init__(db, TenantPlan)

    def get_by_code(self, code: str) -> Optional[TenantPlan]:
        """根据code获取套餐"""
        return self.db.execute(
            select(TenantPlan).filter(TenantPlan.code == code)
        ).scalar_one_or_none()

    def get_active_plans(self) -> list[TenantPlan]:
        """获取所有启用的套餐"""
        return self.db.execute(
            select(TenantPlan).filter(TenantPlan.is_active).order_by(TenantPlan.price_monthly)
        ).scalars().all()


class TenantRepository(BaseRepository[Tenant]):
    """租户Repository"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        super().__init__(db, Tenant)

    def get_paginated_with_filters(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str = None,
        status: str = None,
        plan_id: str = None,
    ) -> Tuple[List[Tenant], int]:
        """分页获取租户列表"""
        query = select(Tenant).options(joinedload(Tenant.plan))
        if search:
            query = query.filter(
                Tenant.name.ilike(f"%{search}%")
                | Tenant.contact_email.ilike(f"%{search}%")
                | Tenant.domain.ilike(f"%{search}%")
            )
        if status:
            query = query.filter(Tenant.status == status)
        if plan_id:
            query = query.filter(Tenant.plan_id == plan_id)

        total = self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        items = (
            self.db.execute(
                query.order_by(Tenant.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return items, total or 0

    def get_by_domain(self, domain: str) -> Optional[Tenant]:
        """根据domain获取租户"""
        return self.db.execute(
            select(Tenant).filter(Tenant.domain == domain)
        ).scalar_one_or_none()

    def get_stats(self) -> dict[str, Any]:
        """获取租户统计"""
        now = datetime.now(timezone.utc)
        thirty_days_later = now + timedelta(days=30)
        total = self.db.scalar(select(func.count(Tenant.id)))
        active = self.db.scalar(
            select(func.count(Tenant.id)).filter(
                Tenant.status == "active", Tenant.is_active
            )
        )
        trial = self.db.scalar(
            select(func.count(Tenant.id)).filter(Tenant.status == "trial")
        )
        suspended = self.db.scalar(
            select(func.count(Tenant.id)).filter(Tenant.status == "suspended")
        )
        expiring_soon = self.db.scalar(
            select(func.count(Tenant.id)).filter(
                Tenant.expires_at.isnot(None),
                Tenant.expires_at <= thirty_days_later,
                Tenant.expires_at > now,
                Tenant.is_active,
            )
        )
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_this_month = self.db.scalar(
            select(func.count(Tenant.id)).filter(Tenant.created_at >= month_start)
        )
        # 本月实收（分）：真实台账优先，无台账时用非 mock 已支付订单
        monthly_revenue_cents = self.db.scalar(
            select(func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0)).filter(
                *revenue_ledger_conditions(self.db),
                FinanceLedgerEntry.recorded_at >= month_start,
            )
        ) or 0
        if monthly_revenue_cents <= 0:
            paid_q = self.db.query(PaymentOrder).filter(
                PaymentOrder.status == "paid",
                PaymentOrder.paid_at >= month_start,
            )
            monthly_revenue_cents = (
                apply_real_paid_order_filters(paid_q)
                .with_entities(func.coalesce(func.sum(PaymentOrder.amount), 0))
                .scalar()
            ) or 0

        return {
            "total_tenants": total or 0,
            "active_tenants": active or 0,
            "trial_tenants": trial or 0,
            "suspended_tenants": suspended or 0,
            "expiring_soon": expiring_soon or 0,
            "new_tenants_this_month": new_this_month or 0,
            "monthly_revenue": int(monthly_revenue_cents),
        }


class TenantSubscriptionRepository(BaseRepository[TenantSubscription]):
    """订阅Repository"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        super().__init__(db, TenantSubscription)

    def get_active_by_tenant(self, tenant_id: str) -> Optional[TenantSubscription]:
        """获取租户当前有效订阅"""
        return self.db.execute(
            select(TenantSubscription).filter(
                TenantSubscription.tenant_id == tenant_id,
                TenantSubscription.status == "active",
            )
        ).scalar_one_or_none()


class TenantInvoiceRepository(BaseRepository[TenantInvoice]):
    """账单Repository"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        super().__init__(db, TenantInvoice)

    def get_paginated_by_tenant(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[TenantInvoice], int]:
        """分页获取租户账单"""
        query = (
            select(TenantInvoice)
            .options(joinedload(TenantInvoice.subscription))
            .filter(TenantInvoice.tenant_id == tenant_id)
        )
        total = self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        items = (
            self.db.execute(
                query.order_by(TenantInvoice.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return items, total or 0
