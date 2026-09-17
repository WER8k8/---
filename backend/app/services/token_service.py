# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户 Token 配额与账本"""

import json

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.token_ledger import TokenLedgerEntry

TOKEN_SUSPEND_REASON = "token_depleted"


class InsufficientTokenError(Exception):
    pass


class TokenService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    @staticmethod
    def _read_settings(tenant: Tenant) -> dict:
        """_read_settings。

        参数说明：
        :param tenant: 参数 tenant
        :return: 返回处理结果。
        """
        raw = tenant.settings or "{}"
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _write_settings(tenant: Tenant, data: dict) -> None:
        """_write_settings。

        参数说明：
        :param tenant: 参数 tenant
        :param data: 参数 data
        :return: 返回处理结果。
        """
        tenant.settings = json.dumps(data, ensure_ascii=False)

    def _maybe_suspend_for_depleted_tokens(self, tenant: Tenant, balance: int) -> None:
        """_maybe_suspend_for_depleted_tokens。

        参数说明：
        :param self: 参数 self
        :param tenant: 参数 tenant
        :param balance: 参数 balance
        :return: 返回处理结果。
        """
        if balance > 0:
            return
        if tenant.status not in ("active", "trial"):
            return
        tenant.status = "suspended"
        cfg = self._read_settings(tenant)
        cfg["suspend_reason"] = TOKEN_SUSPEND_REASON
        self._write_settings(tenant, cfg)

    def _maybe_restore_after_token_credit(self, tenant: Tenant, balance: int) -> None:
        """_maybe_restore_after_token_credit。

        参数说明：
        :param self: 参数 self
        :param tenant: 参数 tenant
        :param balance: 参数 balance
        :return: 返回处理结果。
        """
        if balance <= 0:
            return
        cfg = self._read_settings(tenant)
        if cfg.get("suspend_reason") != TOKEN_SUSPEND_REASON:
            return
        cfg.pop("suspend_reason", None)
        self._write_settings(tenant, cfg)
        if tenant.status == "suspended":
            tenant.status = "active"

    def _quota_limit(self, tenant: Tenant) -> int:
        """_quota_limit。

        参数说明：
        :param self: 参数 self
        :param tenant: 参数 tenant
        :return: 返回处理结果。
        """
        base = int(tenant.plan.max_ai_quota) if tenant.plan and tenant.plan.max_ai_quota else 0
        bonus = int(tenant.purchased_token_bonus or 0)
        return base + bonus

    def balance(self, tenant_id: str) -> int:
        """balance。

        参数说明：
        :param self: 参数 self
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return 0
        if tenant.status == "suspended":
            return 0
        return max(0, self._quota_limit(tenant) - int(tenant.ai_quota_used or 0))

    def ensure_can_consume(self, tenant_id: str, amount: int) -> None:
        """ensure_can_consume。

        参数说明：
        :param self: 参数 self
        :param tenant_id: 参数 tenant_id
        :param amount: 参数 amount
        :return: 返回处理结果。
        """
        if amount <= 0:
            return
        if self.balance(tenant_id) < amount:
            raise InsufficientTokenError("Token 余额不足，请充值或升级套餐")

    def consume(self, tenant_id: str, amount: int, reason: str, reference_id: str | None = None) -> int:
        """consume。

        参数说明：
        :param self: 参数 self
        :param tenant_id: 参数 tenant_id
        :param amount: 参数 amount
        :param reason: 参数 reason
        :param reference_id: 参数 reference_id
        :return: 返回处理结果。
        """
        self.ensure_can_consume(tenant_id, amount)
        # BUG-17 修复：加行锁防止并发超卖
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).with_for_update().first()
        if not tenant:
            raise ValueError(f"租户不存在: tenant_id={tenant_id}")
        tenant.ai_quota_used = int(tenant.ai_quota_used or 0) + amount
        bal = self.balance(tenant_id)
        self.db.add(
            TokenLedgerEntry(
                tenant_id=tenant_id,
                delta=-amount,
                balance_after=bal,
                reason=reason,
                reference_id=reference_id,
            )
        )
        self._maybe_suspend_for_depleted_tokens(tenant, bal)
        self.db.commit()
        return bal

    def credit(
        self,
        tenant_id: str,
        amount: int,
        reason: str,
        reference_id: str | None = None,
    ) -> int:
        """增加配额（充值 / bonus，不再下界截断吞额度）。"""
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError("租户不存在")
        bonus = int(tenant.purchased_token_bonus or 0) + amount
        tenant.purchased_token_bonus = bonus
        avail = max(0, self._quota_limit(tenant) - int(tenant.ai_quota_used or 0))
        self._maybe_restore_after_token_credit(tenant, avail)
        bal = self.balance(tenant_id)
        self.db.add(
            TokenLedgerEntry(
                tenant_id=tenant_id,
                delta=amount,
                balance_after=bal,
                reason=reason,
                reference_id=reference_id,
            )
        )
        self.db.commit()
        return bal
