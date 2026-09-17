# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""摸金校尉 · 生产就绪检查 + 平台自营租户 bootstrap。"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import case as case_when, or_
from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.core.config import settings
from app.models.content import PlatformAccount
from app.models.tenant import Tenant, TenantPlan
from app.services.hermes.greedy_avatar_constitution import assert_greedy_action

logger = logging.getLogger("uj-admin.greedy_readiness")

_BOOTSTRAP_TENANT_DOMAIN = "platform-survival.ops"
_BOOTSTRAP_REDIS_KEY = "hermes:greedy:publish_tenant_id"
_fallback_tenant_id: str | None = None


def _check(name: str, ok: bool, *, message: str, severity: str = "required") -> dict[str, Any]:
    """_check。

    参数说明：
    :param name: 参数 name
    :param ok: 参数 ok
    :param message: 参数 message
    :param severity: 参数 severity
    :return: 返回处理结果。
    """
    return {"id": name, "ok": ok, "message": message, "severity": severity}


def ensure_greedy_publish_tenant(db: Session, *, force: bool = False) -> dict[str, Any]:
    """创建或返回平台 survival 自营租户（domain=platform-survival.ops）。"""
    assert_greedy_action("write_greedy_snapshot")
    configured = (getattr(settings, "HERMES_GREEDY_PUBLISH_TENANT_ID", None) or "").strip()
    if configured and not force:
        row = db.query(Tenant).filter(Tenant.id == configured, Tenant.is_active.is_(True)).first()
        if row:
            return {"ok": True, "tenant_id": configured, "source": "env", "domain": row.domain}

    existing = (
        db.query(Tenant)
        .filter(Tenant.domain == _BOOTSTRAP_TENANT_DOMAIN, Tenant.is_active.is_(True))
        .first()
    )
    if existing and not force:
        _persist_bootstrap_tenant_id(str(existing.id))
        return {
            "ok": True,
            "tenant_id": str(existing.id),
            "source": "existing_domain",
            "domain": existing.domain,
            "name": existing.name,
        }

    plan = (
        db.query(TenantPlan)
        .filter(
            or_(
                TenantPlan.code == "enterprise",
                TenantPlan.is_active.is_(True),
            )
        )
        .order_by(
            case_when(TenantPlan.code == "enterprise", 0, else_=1),
            TenantPlan.id.asc(),
        )
        .first()
    )
    if not plan:
        plan = TenantPlan(
            name="平台自营",
            code="platform_ops",
            price_monthly=0,
            price_yearly=0,
            features='["seo","publish","ubrain"]',
            is_active=True,
        )
        db.add(plan)
        db.flush()

    tenant = Tenant(
        id=str(uuid.uuid4()),
        name="摸金校尉·平台自营",
        domain=_BOOTSTRAP_TENANT_DOMAIN,
        plan_id=plan.id,
        status="active",
        is_active=True,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    tid = str(tenant.id)
    _persist_bootstrap_tenant_id(tid)
    logger.info("Greedy publish tenant bootstrapped id=%s domain=%s", tid, _BOOTSTRAP_TENANT_DOMAIN)
    return {
        "ok": True,
        "tenant_id": tid,
        "source": "created",
        "domain": tenant.domain,
        "name": tenant.name,
        "env_hint": f"HERMES_GREEDY_PUBLISH_TENANT_ID={tid}",
    }


def _persist_bootstrap_tenant_id(tenant_id: str) -> None:
    """_persist_bootstrap_tenant_id。

    参数说明：
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    global _fallback_tenant_id
    _fallback_tenant_id = tenant_id
    if redis_client:
        try:
            redis_client.set(_BOOTSTRAP_REDIS_KEY, tenant_id, ex=86400 * 365)
        except Exception:
            pass


def resolve_bootstrap_tenant_id_from_store() -> str | None:
    """resolve_bootstrap_tenant_id_from_store。
    :return: 返回处理结果。
    """
    if redis_client:
        try:
            raw = redis_client.get(_BOOTSTRAP_REDIS_KEY)
            if raw:
                return raw.decode() if isinstance(raw, bytes) else str(raw)
        except Exception:
            pass
    return _fallback_tenant_id


def bootstrap_publish_platform_accounts(db: Session, *, tenant_id: str, locale: str = "global") -> dict[str, Any]:
    """为自营租户 bootstrap 平台 + 占位账号（便于 PublishTask 排队）。"""
    assert_greedy_action("publish_survival_marketing")
    from app.services.hermes.greedy_survival_publish_service import channels_to_platform_names
    from app.services.ubrain.matrix_publish_bootstrap import (
        ensure_matrix_content_draft,
        ensure_placeholder_accounts,
        ensure_platforms_for_names,
    )
    names = channels_to_platform_names(["website_embed", "linkedin_carousel", "independent_landing"], locale=locale)
    region = "cn" if locale.startswith("zh") else "global"
    platform_ids = ensure_platforms_for_names(db, names, region=region)
    stubs = ensure_placeholder_accounts(db, tenant_id=tenant_id, platform_ids=platform_ids)
    master_id = ensure_matrix_content_draft(
        db,
        tenant_id=tenant_id,
        message="Platform survival marketing — 摸金校尉自营矩阵",
        product_hint="B2B survival monetization",
    )
    return {
        "ok": True,
        "tenant_id": tenant_id,
        "platform_ids": platform_ids,
        "platform_names": names,
        "stub_accounts": stubs,
        "content_master_id": master_id,
    }


def greedy_production_readiness(db: Session) -> dict[str, Any]:
    """生产 checklist — 供 Admin / 脚本 / 上线前核对。"""
    assert_greedy_action("read_probe")
    checks: list[dict[str, Any]] = []
    checks, tenant_row, publish_tid, bootstrap_tid, greedy_on = _build_readiness_checks_part_a(db)
    checks = _build_readiness_checks_part_b(checks)
    required_fail = [c for c in checks if c["severity"] == "required" and not c["ok"]]
    ready = len(required_fail) == 0 and greedy_on
    return {
        "ready": ready,
        "environment": settings.ENVIRONMENT,
        "checks": checks,
        "publish_tenant_id": str(tenant_row.id) if tenant_row else publish_tid or bootstrap_tid,
        "publish_tenant_domain": tenant_row.domain if tenant_row else _BOOTSTRAP_TENANT_DOMAIN,
        "worldfirst_setup": _worldfirst_hints(),
        "env_template_path": "deploy/production/env.template",
        "admin_hub": "/admin/system/greedy-hub",
    }


def _worldfirst_hints() -> dict[str, Any]:
    """_worldfirst_hints。
    :return: 返回处理结果。
    """
    try:
        from app.services.hermes.platform_survival_service import worldfirst_setup_hints
        return worldfirst_setup_hints()
    except Exception as exc:
        return {"error": str(exc)[:120]}

def _build_readiness_checks_part_a(db: Session) -> tuple[list[dict[str, Any]], Any, str, str, bool]:
    """_build_readiness_checks_part_a。

    参数说明：
    :return: 返回 (checks, tenant_row, publish_tid, bootstrap_tid, greedy_on)。
    """
    greedy_on = bool(getattr(settings, "HERMES_GREEDY_AVATAR_ENABLED", True))
    checks.append(_check("greedy_avatar_enabled", greedy_on, message="HERMES_GREEDY_AVATAR_ENABLED"))
    wf_secret = (getattr(settings, "SURVIVAL_WORLDFIRST_WEBHOOK_SECRET", None) or "").strip()
    checks.append(
        _check(
            "worldfirst_webhook_secret",
            bool(wf_secret),
            message="SURVIVAL_WORLDFIRST_WEBHOOK_SECRET（L6 自动入账）",
            severity="required",
        )
    )
    feishu = (
        (getattr(settings, "HERMES_GREEDY_DIGEST_WEBHOOK_URL", None) or "").strip()
        or (getattr(settings, "FEISHU_WEBHOOK_URL", None) or "").strip()
    )
    checks.append(
        _check(
            "feishu_digest_webhook",
            bool(feishu),
            message="FEISHU_WEBHOOK_URL 或 HERMES_GREEDY_DIGEST_WEBHOOK_URL",
            severity="recommended",
        )
    )
    publish_tid = (getattr(settings, "HERMES_GREEDY_PUBLISH_TENANT_ID", None) or "").strip()
    bootstrap_tid = resolve_bootstrap_tenant_id_from_store()
    tenant_row = None
    if publish_tid:
        tenant_row = db.query(Tenant).filter(Tenant.id == publish_tid).first()
    elif bootstrap_tid:
        tenant_row = db.query(Tenant).filter(Tenant.id == bootstrap_tid).first()
    else:
        tenant_row = db.query(Tenant).filter(Tenant.domain == _BOOTSTRAP_TENANT_DOMAIN).first()

    checks.append(
        _check(
            "publish_tenant",
            tenant_row is not None,
            message="HERMES_GREEDY_PUBLISH_TENANT_ID 或 bootstrap 租户 platform-survival.ops",
            severity="required",
        )
    )
    acct_count = 0
    if tenant_row:
        acct_count = (
            db.query(PlatformAccount)
            .filter(PlatformAccount.tenant_id == str(tenant_row.id), PlatformAccount.is_active.is_(True))
            .count()
        )
    checks.append(
        _check(
            "publish_platform_accounts",
            acct_count > 0,
            message=f"自营租户 platform_account 数={acct_count}（可 POST bootstrap 补占位）",
            severity="recommended",
        )
    )
    checks.append(
        _check(
            "redis",
            redis_client is not None,
            message="Redis（队列/大赛记忆/累计）",
            severity="required",
        )
    )
    checks.append(
        _check(
            "endurance_scheduler",
            settings.greedy_endurance_scheduler_active,
            message="HERMES_GREEDY_ENDURANCE_SCHEDULER_ENABLED（生产默认开）",
            severity="recommended",
        )
    )
    return checks, tenant_row, publish_tid, bootstrap_tid, greedy_on


def _build_readiness_checks_part_b(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """_build_readiness_checks_part_b。

    参数说明：
    :return: 返回更新后的 checks。
    """
    checks.append(
        _check(
            "revenue_loop_scheduler",
            settings.greedy_revenue_loop_scheduler_active,
            message="HERMES_GREEDY_REVENUE_LOOP_SCHEDULER_ENABLED",
            severity="recommended",
        )
    )
    checks.append(
        _check(
            "digest_scheduler",
            settings.greedy_survival_digest_scheduler_active,
            message="HERMES_GREEDY_DIGEST_SCHEDULER_ENABLED",
            severity="recommended",
        )
    )
    cron_token = (getattr(settings, "OPS_CRON_TOKEN", None) or "").strip()
    checks.append(
        _check(
            "ops_cron_token",
            bool(cron_token),
            message="OPS_CRON_TOKEN（外部 cron 搞钱闭环）",
            severity="optional",
        )
    )
    auto_pub = getattr(settings, "HERMES_GREEDY_AUTO_PUBLISH_ENABLED", None)
    checks.append(
        _check(
            "auto_publish_off_by_default",
            auto_pub is not True,
            message="HERMES_GREEDY_AUTO_PUBLISH_ENABLED=false（人工审核 L4，符合预期）",
            severity="optional",
        )
    )
    return checks

