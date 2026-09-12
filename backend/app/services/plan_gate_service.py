"""Plan Gate — 套餐功能校验（BE-04）

边界：只读 tenant.plan + plan_catalog；不修改租户状态。
"""

from __future__ import annotations

from typing import Any

from app.api.v1.admin_bff.plan_catalog import PLAN_FEATURES
from app.models.tenant import Tenant

PLAN_ORDER = ("trial", "starter", "pro", "enterprise")

# 功能键 → 最低套餐（与 docs/saas-plan-gate-fields-v1.md 对齐）
FEATURE_MIN_PLAN: dict[str, str] = {
    "domain_bind": "trial",
    "publish_limited": "trial",
    "inquiry_limited": "trial",
    "publish": "starter",
    "inquiry": "starter",
    "im": "pro",
    "seo_matrix": "pro",
    "geo_submit_limited": "trial",
    "geo_engine": "pro",
    "geo_content_matrix": "pro",
    "geo_submit_pack": "pro",
    "geo_monitor": "enterprise",
    "media_factory": "pro",
    "video_matrix": "pro",
    "egress_ip": "enterprise",
    "white_label": "enterprise",
    "audit_log": "enterprise",
}

# API / 路由前缀 → 功能键
ROUTE_FEATURE_MAP: dict[str, str] = {
    "/client/egress": "egress_ip",
    "/client/publish": "geo_content_matrix",
    "/client/copilot": "geo_content_matrix",
    "/client/media-factory": "media_factory",
    "/client/article-to-video": "media_factory",
    "/client/ai-scenarios": "seo_matrix",
    "/client/video-matrix": "video_matrix",
}


def _plan_rank(code: str) -> int:
    """_plan_rank。

    参数说明：
    :param code: 参数 code
    :return: 返回处理结果。
    """
    try:
        return PLAN_ORDER.index(code)
    except ValueError:
        return 0


def tenant_plan_code(tenant: Tenant | None) -> str:
    """tenant_plan_code。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant or not tenant.plan:
        return "trial"
    return tenant.plan.code or "trial"


def required_plan_for_feature(feature_key: str) -> str:
    """required_plan_for_feature。

    参数说明：
    :param feature_key: 参数 feature_key
    :return: 返回处理结果。
    """
    return FEATURE_MIN_PLAN.get(feature_key, "enterprise")


def tenant_has_feature(tenant: Tenant | None, feature_key: str) -> bool:
    """tenant_has_feature。

    参数说明：
    :param tenant: 参数 tenant
    :param feature_key: 参数 feature_key
    :return: 返回处理结果。
    """
    current = tenant_plan_code(tenant)
    required = required_plan_for_feature(feature_key)
    if _plan_rank(current) < _plan_rank(required):
        return False
    plan_feats = PLAN_FEATURES.get(current, {}).get("features", [])
    if feature_key in plan_feats:
        return True
    if required == current:
        return True
    return _plan_rank(current) >= _plan_rank(required)


def evaluate_feature_access(tenant: Tenant | None, feature_key: str) -> dict[str, Any]:
    """evaluate_feature_access。

    参数说明：
    :param tenant: 参数 tenant
    :param feature_key: 参数 feature_key
    :return: 返回处理结果。
    """
    allowed = tenant_has_feature(tenant, feature_key)
    required = required_plan_for_feature(feature_key)
    current = tenant_plan_code(tenant)
    required_name = PLAN_FEATURES.get(required, {}).get("name", required)
    return {
        "allowed": allowed,
        "feature_key": feature_key,
        "current_plan": current,
        "current_plan_name": PLAN_FEATURES.get(current, {}).get("name", current),
        "required_plan": required,
        "required_plan_name": required_name,
        "cta_copy": f"该能力属于 {required_name}，升级后立即可用。",
    }


def evaluate_route_access(tenant: Tenant | None, path: str) -> dict[str, Any] | None:
    """evaluate_route_access。

    参数说明：
    :param tenant: 参数 tenant
    :param path: 参数 path
    :return: 返回处理结果。
    """
    normalized = path.split("?")[0].rstrip("/") or "/"
    feature = ROUTE_FEATURE_MAP.get(normalized)
    if not feature:
        for prefix, fk in ROUTE_FEATURE_MAP.items():
            if normalized.startswith(prefix):
                feature = fk
                break
    if not feature:
        return None
    return evaluate_feature_access(tenant, feature)


def evaluate_ai_quota(tenant: Tenant | None) -> dict[str, Any]:
    """AI 配额判定（只读，轮22 计量埋点路由到本服务）。

    能力开关走套餐门槛（AI 场景能力挂 seo_matrix）；额度取 tenant.plan.max_ai_quota
    与 tenant.ai_quota_used；不修改任何租户状态。
    """
    feature_allowed = tenant_has_feature(tenant, "seo_matrix")
    max_quota = (tenant.plan.max_ai_quota if tenant and tenant.plan else 0) or 0
    used = (tenant.ai_quota_used if tenant else 0) or 0
    quota_ok = max_quota <= 0 or used < max_quota
    allowed = feature_allowed and quota_ok
    return {
        "allowed": allowed,
        "feature_allowed": feature_allowed,
        "max_ai_quota": max_quota,
        "used": used,
        "remaining": max(0, max_quota - used) if max_quota > 0 else None,
        "feature_key": "seo_matrix",
    }
