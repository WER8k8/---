# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""注册后后台 autopilot — 0 等待进向导。"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def _safe_settings(raw: str | None) -> dict:
    """_safe_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def get_autopilot_job(tenant) -> dict[str, Any] | None:
    """get_autopilot_job。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    onboarding = _safe_settings(tenant.settings).get("onboarding") or {}
    job = onboarding.get("autopilot_job")
    return job if isinstance(job, dict) else None


def set_autopilot_job(db, tenant_id: str, patch: dict[str, Any]) -> None:
    """set_autopilot_job。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param patch: 参数 patch
    :return: 返回处理结果。
    """
    from app.models.tenant import Tenant
    row = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not row:
        return
    settings = _safe_settings(row.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    job = onboarding.get("autopilot_job") if isinstance(onboarding.get("autopilot_job"), dict) else {}
    job.update(patch)
    onboarding["autopilot_job"] = job
    settings["onboarding"] = onboarding
    row.settings = json.dumps(settings, ensure_ascii=False)
    row.updated_at = _utcnow()
    db.add(row)
    db.commit()


def schedule_autopilot_after_register(
    *,
    tenant_id: str,
    user_id: str,
    product_name: str,
) -> None:
    """注册 commit 后后台跑一键开业（daemon thread）。"""
    def _worker() -> None:
        """_worker。
        :return: 返回处理结果。
        """
        from app.db.session import SessionLocal
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.services.onboarding_autopilot_service import run_onboarding_autopilot
        db = SessionLocal()
        try:
            set_autopilot_job(
                db,
                tenant_id,
                {
                    "status": "running",
                    "started_at": _utcnow().isoformat(),
                    "product": product_name,
                },
            )
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            user = db.query(User).filter(User.id == user_id).first()
            if not tenant or not user:
                set_autopilot_job(
                    db,
                    tenant_id,
                    {"status": "failed", "error": "tenant_or_user_missing"},
                )
                return
            result = asyncio.run(
                run_onboarding_autopilot(
                    db,
                    tenant,
                    user,
                    product_name=product_name,
                    skip_hermes=False,
                )
            )
            set_autopilot_job(
                db,
                tenant_id,
                {
                    "status": "done" if result.get("ok") else "partial",
                    "finished_at": _utcnow().isoformat(),
                    "headline": result.get("headline"),
                },
            )
        except Exception as exc:
            logger.exception("Background autopilot failed tenant=%s", tenant_id)
            try:
                set_autopilot_job(
                    db,
                    tenant_id,
                    {"status": "failed", "error": str(exc)[:200]},
                )
            except Exception:
                pass
        finally:
            db.close()

    threading.Thread(target=_worker, daemon=True, name=f"autopilot-{tenant_id[:8]}").start()


def run_onboarding_autopilot_job(
    *,
    tenant_id: str,
    user_id: str,
    product_name: str = "",
) -> dict[str, Any]:
    """供调度任务调用的入驻自动化函数。"""
    schedule_autopilot_after_register(
        tenant_id=tenant_id,
        user_id=user_id,
        product_name=product_name,
    )
    return {"tenant_id": tenant_id, "status": "scheduled", "product_name": product_name}
