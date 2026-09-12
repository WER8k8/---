"""支付成功后自动开户 / 续费"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.finance_ledger import FinanceLedgerEntry
from app.models.payment import PaymentOrder
from app.models.referral import ReferralRecord
from app.models.tenant import Tenant, TenantPlan, TenantSubscription
from app.services.agent_commission_service import accrue_commission_for_payment
from app.services.order_addon_service import apply_order_addon
from app.services.egress_quota_service import auto_assign_slots_for_tenant
from app.services.token_service import TokenService


class ProvisioningService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def provision_after_payment(self, order: PaymentOrder) -> dict:
        """provision_after_payment。

        参数说明：
        :param self: 参数 self
        :param order: 参数 order
        :return: 返回处理结果。
        """
        tenant = self.db.query(Tenant).filter(Tenant.id == order.tenant_id).first()
        if not tenant:
            return {"ok": False, "reason": "tenant_not_found"}

        sub = None
        if order.subscription_id:
            sub = self.db.query(TenantSubscription).filter_by(id=order.subscription_id).first()

        if sub:
            tenant.plan_id = sub.plan_id
            tenant.status = "active"
            tenant.is_active = True
            tenant.subscribed_at = tenant.subscribed_at or datetime.now(timezone.utc)
            cycle_days = 365 if sub.billing_cycle == "yearly" else 30
            tenant.expires_at = datetime.now(timezone.utc) + timedelta(days=cycle_days)
            plan = self.db.query(TenantPlan).filter(TenantPlan.id == sub.plan_id).first()
            if plan:
                tenant.ai_quota_used = 0  # 续费重置当月额度计数

        if not self.db.query(FinanceLedgerEntry).filter(
            FinanceLedgerEntry.reference_id == order.order_no,
            FinanceLedgerEntry.entry_type == "revenue",
        ).first():
            from app.services.order_addon_service import is_addon_order, parse_token_amount
            from app.services.egress_addon_service import parse_addon_slots
            if parse_token_amount(order.subject):
                category = "token_pack"
            elif parse_addon_slots(order.subject):
                category = "egress_addon"
            elif is_addon_order(order):
                category = "addon"
            else:
                category = "subscription"
            self.db.add(
                FinanceLedgerEntry(
                    entry_type="revenue",
                    category=category,
                    amount_cents=order.amount,
                    tenant_id=tenant.id,
                    reference_id=order.order_no,
                    note=order.subject,
                )
            )

        commission = None
        from app.services.order_addon_service import is_addon_order
        if not is_addon_order(order):
            commission = accrue_commission_for_payment(self.db, order)

        addon_result = apply_order_addon(self.db, order)
        referral_applied = self._apply_referral_rewards(tenant.id)
        egress_assigned = 0
        if not addon_result:
            egress_assigned = auto_assign_slots_for_tenant(self.db, tenant)
        self.db.commit()
        return {
            "ok": True,
            "tenant_id": tenant.id,
            "status": tenant.status,
            "expires_at": tenant.expires_at.isoformat() if tenant.expires_at else None,
            "referral_rewards": referral_applied,
            "egress_slots_assigned": egress_assigned,
            "addon": addon_result,
            "agent_commission": commission,
        }

    def _apply_referral_rewards(self, paid_tenant_id: str) -> int:
        """_apply_referral_rewards。

        参数说明：
        :param self: 参数 self
        :param paid_tenant_id: 参数 paid_tenant_id
        :return: 返回处理结果。
        """
        record = (
            self.db.query(ReferralRecord)
            .filter(
                ReferralRecord.invited_tenant_id == paid_tenant_id,
                ReferralRecord.status == "pending",
            )
            .first()
        )
        if not record:
            return 0
        inviter = self.db.query(Tenant).filter(Tenant.id == record.inviter_tenant_id).first()
        if inviter:
            TokenService(self.db).credit(inviter.id, 5000, "referral_first_payment")
            record.status = "rewarded"
            record.reward_type = "token"
            record.reward_amount = 5000
            record.rewarded_at = datetime.now(timezone.utc)
        self.db.commit()
        return 1
