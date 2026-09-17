# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户订阅生命周期：到期冻结、试用结束处理。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.tenant import Tenant


class TenantLifecycleService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def enforce_expired_subscriptions(self, *, dry_run: bool = False) -> dict:
        """将已过期的 active/trial 租户标记为 suspended。"""
        now = datetime.now(timezone.utc)
        q = self.db.query(Tenant).filter(
            Tenant.expires_at.isnot(None),
            Tenant.expires_at < now,
            Tenant.status.in_(("active", "trial")),
        )
        tenants = q.all()
        ids = [t.id for t in tenants]
        if not dry_run and tenants:
            for tenant in tenants:
                tenant.status = "suspended"
                tenant.is_active = False
            self.db.commit()
        return {
            "checked_at": now.isoformat(),
            "suspended_count": len(ids),
            "tenant_ids": ids,
            "dry_run": dry_run,
        }

    def enforce_trial_expiry(self, *, dry_run: bool = False) -> dict:
        """试用到期且未付费 → suspended。"""
        now = datetime.now(timezone.utc)
        q = self.db.query(Tenant).filter(
            Tenant.status == "trial",
            Tenant.trial_ends_at.isnot(None),
            Tenant.trial_ends_at < now,
        )
        tenants = q.all()
        ids = [t.id for t in tenants]
        if not dry_run and tenants:
            for tenant in tenants:
                tenant.status = "suspended"
                tenant.is_active = False
            self.db.commit()
        return {
            "checked_at": now.isoformat(),
            "suspended_count": len(ids),
            "tenant_ids": ids,
            "dry_run": dry_run,
        }

    def preview_expiring(self, *, within_days: int = 7) -> dict:
        """即将到期租户（供管理端提醒，不冻结）。"""
        now = datetime.now(timezone.utc)
        horizon = now + timedelta(days=within_days)
        rows = (
            self.db.query(Tenant)
            .filter(
                Tenant.expires_at.isnot(None),
                Tenant.expires_at >= now,
                Tenant.expires_at <= horizon,
                Tenant.status.in_(("active", "trial")),
            )
            .order_by(Tenant.expires_at.asc())
            .limit(50)
            .all()
        )
        return {
            "within_days": within_days,
            "count": len(rows),
            "tenants": [
                {
                    "id": t.id,
                    "name": t.name,
                    "domain": t.domain,
                    "expires_at": t.expires_at.isoformat() if t.expires_at else None,
                    "status": t.status,
                }
                for t in rows
            ],
        }

    def run_all(self, *, dry_run: bool = False) -> dict:
        """run_all。

        参数说明：
        :param self: 参数 self
        :param dry_run: 参数 dry_run
        :return: 返回处理结果。
        """
        sub = self.enforce_expired_subscriptions(dry_run=dry_run)
        trial = self.enforce_trial_expiry(dry_run=dry_run)
        return {
            "subscription": sub,
            "trial": trial,
            "total_suspended": sub["suspended_count"] + trial["suspended_count"],
            "expiring_soon": self.preview_expiring(within_days=7),
        }
