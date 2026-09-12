"""超级管理员后台 API - 统一路由分组"""

from fastapi import APIRouter

from app.api.v1.super_admin.ai_config import router as ai_config_router
from app.api.v1.super_admin.ai_cost import router as ai_cost_router
from app.api.v1.super_admin.agent import router as agent_router
from app.api.v1.super_admin.alerts import router as alerts_router
from app.api.v1.super_admin.audit import router as audit_router
from app.api.v1.super_admin.backup import router as backup_router
from app.api.v1.super_admin.geo_engine import router as geo_engine_router
from app.api.v1.super_admin.langchain import router as langchain_router
from app.api.v1.super_admin.products import router as products_router
from app.api.v1.super_admin.auth import router as auth_router
from app.api.v1.super_admin.cc_switch import router as cc_switch_router
from app.api.v1.super_admin.dashboard import router as dashboard_router
from app.api.v1.super_admin.menus import router as menus_router
from app.api.v1.super_admin.monitor import router as monitor_router
from app.api.v1.super_admin.permissions import router as permissions_router
from app.api.v1.super_admin.reports import router as reports_router
from app.api.v1.super_admin.search import router as search_router
from app.api.v1.super_admin.seo_proxy import router as seo_proxy_router
from app.api.v1.super_admin.users import router as users_router
from app.api.v1.super_admin.v2ray_tracker import router as v2ray_tracker_router
from app.api.v1.super_admin.v2ray_subscriptions import router as v2ray_subscriptions_router
from app.api.v1.super_admin.tenants import router as tenants_router
from app.api.v1.super_admin.platform_registry import router as platform_registry_router
from app.api.v1.super_admin.aggregation import router as aggregation_router
from app.api.v1.super_admin.storage_provision import router as storage_provision_router

router = APIRouter(prefix="/super-admin", tags=["超级管理员后台"])

router.include_router(auth_router, prefix="/auth")
router.include_router(menus_router, prefix="/menus")
router.include_router(permissions_router, prefix="/permissions")
router.include_router(users_router, prefix="/users")
router.include_router(dashboard_router, prefix="/dashboard")
router.include_router(ai_config_router, prefix="/ai-config")
router.include_router(ai_cost_router, prefix="/ai-cost")
router.include_router(ai_cost_router, prefix="/ai-usage")
router.include_router(cc_switch_router, prefix="/cc-switch")
router.include_router(langchain_router, prefix="/langchain")
router.include_router(monitor_router, prefix="/monitor")
router.include_router(agent_router, prefix="/agent")
router.include_router(alerts_router, prefix="/alerts")
router.include_router(reports_router, prefix="/reports")
router.include_router(search_router, prefix="/search")
router.include_router(seo_proxy_router, prefix="/seo-proxy")
router.include_router(geo_engine_router, prefix="/geo-engine")
router.include_router(products_router, prefix="/products")
router.include_router(backup_router, prefix="/backup")
router.include_router(audit_router, prefix="/audit")
router.include_router(v2ray_tracker_router, prefix="/v2ray-tracker")
router.include_router(v2ray_subscriptions_router, prefix="/v2ray")
router.include_router(tenants_router, prefix="/tenants")
router.include_router(platform_registry_router)
router.include_router(aggregation_router)
router.include_router(storage_provision_router, prefix="/storage-provision")
