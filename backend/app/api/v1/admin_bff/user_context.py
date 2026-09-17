# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""组装 UacUserInfo — 用户域 + 租户域，adapter 层不堆业务细节"""

from __future__ import annotations

from typing import Any, List

from sqlalchemy.orm import Session

from app.api.v1.admin_bff.schemas import UacUserInfo
from app.api.v1.admin_bff.shell import resolve_home_path, resolve_shell
from app.models.tenant import Tenant
from app.models.user import User
from app.services.onboarding_progress_service import build_onboarding_progress
from app.services.tenant_scenario_service import resolve_tenant_id_for_user

# 与 docs/design/client-dashboard-bento-spec.md §3 Onboarding 对齐
_ONBOARDING_TEMPLATE: List[dict[str, str]] = [
    {"id": "site", "title": "做出官网", "route": "/client/onboarding"},
    {"id": "domain", "title": "绑定自己网址", "route": "/client/billing"},
    {"id": "product", "title": "上架产品", "route": "/client/products"},
    {"id": "publish", "title": "发出第一条", "route": "/client/queues/publish"},
    {"id": "inquiry", "title": "客户能联系你", "route": "/inquiries/im-routing"},
    {"id": "im", "title": "销售收得到消息", "route": "/inquiries/im-routing#wecom-push"},
    {"id": "review", "title": "看效果复盘", "route": "/client/dashboard"},
]


def _tenant_has_bound_domain(tenant: Tenant | None) -> bool:
    """_tenant_has_bound_domain。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant:
        return False
    custom = (tenant.custom_domains or "").strip()
    return bool(custom or tenant.domain)


def build_onboarding_steps(tenant: Tenant | None, db: Session | None = None) -> List[dict[str, Any]]:
    """build_onboarding_steps。

    参数说明：
    :param tenant: 参数 tenant
    :param db: 参数 db
    :return: 返回处理结果。
    """
    if db is not None:
        return build_onboarding_progress(db, tenant, _ONBOARDING_TEMPLATE)
    steps: List[dict[str, Any]] = []
    for i, tpl in enumerate(_ONBOARDING_TEMPLATE):
        done = tpl["id"] == "domain" and _tenant_has_bound_domain(tenant)
        steps.append({**tpl, "order": i, "done": done})
    return steps


def build_plan_usage(tenant: Tenant | None) -> dict[str, Any]:
    """build_plan_usage。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant:
        return {}
    plan = tenant.plan
    max_ai = plan.max_ai_quota if plan else 0
    used = tenant.ai_quota_used or 0
    return {
        "plan_code": plan.code if plan else "trial",
        "plan_name": plan.name if plan else "体验版",
        "ai_quota_used": used,
        "ai_quota_max": max_ai,
        "ai_quota_pct": round(used / max_ai * 100, 1) if max_ai else 0.0,
        "status": tenant.status,
        "expires_at": tenant.expires_at.isoformat() if tenant.expires_at else None,
    }


def load_tenant_for_user(db: Session, user: User) -> Tenant | None:
    """load_tenant_for_user。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :return: 返回处理结果。
    """
    tid = resolve_tenant_id_for_user(db, user)
    if not tid:
        return None
    return db.query(Tenant).filter(Tenant.id == tid).first()


def build_uac_user_info(user: User, db: Session) -> UacUserInfo:
    """build_uac_user_info。

    参数说明：
    :param user: 参数 user
    :param db: 参数 db
    :return: 返回处理结果。
    """
    shell = resolve_shell(user)
    roles = [user.role] if user.role else []
    nickname = user.display_name or user.username or ""
    tenant = load_tenant_for_user(db, user)
    tenant_dict = None
    if tenant:
        tenant_dict = {
            "id": str(tenant.id),
            "name": tenant.name,
            "code": tenant.domain,
        }

    uid = str(user.id)
    return UacUserInfo(
        id=uid,
        userId=uid,
        username=user.username or user.email or "",
        nickname=nickname,
        realName=nickname,
        avatar="",
        roles=roles,
        shell=shell,
        homePath=resolve_home_path(shell),
        desc=shell,
        tenant=tenant_dict,
        onboarding_steps=build_onboarding_steps(tenant, db),
        plan_usage=build_plan_usage(tenant),
    )
