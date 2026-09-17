# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SaaS多租户与商业化路由 - 真实数据库实现"""

import uuid
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import APIResponse, error_response, success_response
from app.core.security import create_access_token, get_current_user, get_password_hash
from app.db.session import get_db

# ── 注册限流：5 次/小时/IP ──
_register_rate: dict[str, list[float]] = defaultdict(list)
_REGISTER_LIMIT = 5
_REGISTER_WINDOW = 3600


def _check_register_rate(ip: str) -> None:
    """执行 check_register_rate 相关逻辑处理。
    
    :param ip: IP地址
    :return: 返回处理结果。
    :raises: HTTPException 等异常在错误时抛出。
    """
    now = time.time()
    _register_rate[ip] = [t for t in _register_rate[ip] if now - t < _REGISTER_WINDOW]
    if len(_register_rate[ip]) >= _REGISTER_LIMIT:
        raise HTTPException(429, "注册过于频繁，请 1 小时后再试")
    _register_rate[ip].append(now)
from app.models.tenant import Tenant, TenantSubscription, UserTenant
from app.models.user import User
from app.repositories.tenant_repository import TenantPlanRepository
from app.schemas.tenant import (
    TenantBrandConfig, TenantCreate, TenantInvoiceListResponse,
    TenantInvoiceResponse, TenantListResponse, TenantOverviewResponse,
    TenantPlanCreate, TenantPlanResponse, TenantPlanUpdate,
    TenantPublicResponse, TenantRegisterSchema, TenantResponse,
    TenantSelfUpdate, TenantStatsResponse, TenantUpdate,
    WhiteLabelConfig, WhiteLabelUpdate,
)
from app.services.tenant_service import TenantPlanService, TenantService
from app.services.tenant_scenario_service import (
    build_tenant_scenario_payload,
    write_tenant_overrides,
)
from app.schemas.auth import TokenResponse, UserResponse


def _safe_json_loads(raw: Optional[str]) -> Dict[str, Any]:
    """安全解析 JSON 字符串，失败返回空 dict"""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/tenants"
ROUTE_TAGS = ["SaaS租户"]

router = APIRouter(tags=["SaaS租户管理"])


def _resolve_billing_tenant(db: Session, user: User, tenant_id: Optional[str] = None):
    """租户管理员解析自身租户；超管须显式传 tenant_id。"""
    if user.role in ("admin", "super_admin"):
        if not tenant_id:
            return None, error_response(400, "请指定 tenant_id")
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return None, error_response(404, "租户不存在")
        return tenant, None
    link = (
        db.query(UserTenant)
        .filter(UserTenant.user_id == user.id, UserTenant.is_active)
        .first()
    )
    if not link:
        return None, error_response(403, "未关联租户")
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return None, error_response(404, "租户不存在")
    return tenant, None


class TenantInvoiceGenerateBody(BaseModel):
    period: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    tenant_id: Optional[str] = None


class TenantInvoiceStatusBody(BaseModel):
    status: str = Field(..., pattern="^(pending|paid|overdue|cancelled)$")
    tenant_id: Optional[str] = None


@router.get("/invoices", response_model=APIResponse[TenantInvoiceListResponse])
def list_my_tenant_invoices(
    tenant_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前租户账单列表（租户管理员 / 超管指定 tenant_id）。"""
    tenant, err = _resolve_billing_tenant(db, current_user, tenant_id)
    if err:
        return err
    service = TenantService(db)
    items, total = service.list_invoices(str(tenant.id), page=page, page_size=page_size)
    return success_response(
        data=TenantInvoiceListResponse(
            items=[TenantInvoiceResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post("/invoices/generate")
def generate_tenant_invoice(
    body: TenantInvoiceGenerateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生成月度 SaaS 账单草案。"""
    tenant, err = _resolve_billing_tenant(db, current_user, body.tenant_id)
    if err:
        return err
    service = TenantService(db)
    try:
        inv = service.create_monthly_invoice(str(tenant.id), body.period)
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(
        data=TenantInvoiceResponse.model_validate(inv),
        message=f"已生成 {body.period} 账单",
    )


@router.put("/invoices/{invoice_id}")
def update_tenant_invoice_status(
    invoice_id: str,
    body: TenantInvoiceStatusBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新账单状态（如标记已付）。"""
    tenant, err = _resolve_billing_tenant(db, current_user, body.tenant_id)
    if err:
        return err
    service = TenantService(db)
    try:
        inv = service.update_invoice_status(str(tenant.id), invoice_id, body.status)
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=TenantInvoiceResponse.model_validate(inv), message="账单已更新")


@router.get("/", response_model=APIResponse[TenantOverviewResponse])
def get_tenants_overview(
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    status: str = None,
    plan: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取租户列表 + 概览统计"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = TenantService(db)
    overview = service.get_overview()
    items, total = service.list_tenants(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        plan_id=plan,
    )
    return success_response(
        data=TenantOverviewResponse(
            stats=TenantStatsResponse(**overview["stats"]),
            recent_tenants=overview["recent_tenants"],
        ),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/current")
def get_current_tenant(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户所属租户信息（含可用功能列表）"""
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        # 超管或未关联租户的用户 - 返回所有功能
        return success_response(data={
            "tenant": None,
            "features": [
                "dashboard", "products", "content", "inquiries", "seo",
                "ai_content", "globalization", "international",
                "users", "settings",
            ],
            "role": "super_admin",
        })

    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return success_response(data={"tenant": None, "features": [], "role": link.role})

    features = _safe_json_loads(tenant.plan.features) if tenant.plan and tenant.plan.features else []
    settings_dict = _safe_json_loads(tenant.settings)
    onboarding = settings_dict.get("onboarding") if isinstance(settings_dict.get("onboarding"), dict) else {}
    from app.services.onboarding_progress_service import (
        build_onboarding_roadmap,
        refresh_onboarding_checklist,
    )
    from app.services.onboarding_external_accounts import (
        build_external_accounts,
        build_external_accounts_phases,
    )
    raw_checklist = onboarding.get("checklist") if isinstance(onboarding.get("checklist"), list) else None
    onboarding_payload = dict(onboarding)
    onboarding_payload["checklist"] = refresh_onboarding_checklist(db, tenant, raw_checklist)
    onboarding_payload["roadmap"] = build_onboarding_roadmap(db, tenant, raw_checklist)
    platform_slots = onboarding.get("platforms") if isinstance(onboarding.get("platforms"), list) else []
    platform_names = [str(p.get("platform_name") or "") for p in platform_slots]
    storage = onboarding.get("storage") if isinstance(onboarding.get("storage"), dict) else {}
    region = (storage.get("product_images") or {}).get("storage_region")
    ext = build_external_accounts(tenant, platform_names=platform_names, storage_region=region)
    onboarding_payload["external_accounts"] = ext
    onboarding_payload["external_account_phases"] = build_external_accounts_phases(ext)
    return success_response(data={
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "domain": tenant.domain,
            "status": tenant.status,
            "settings": settings_dict,
        },
        "features": features,
        "role": link.role,
        "onboarding": onboarding_payload,
    })


@router.put("/self")
def update_current_tenant_settings(
    body: TenantSelfUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """租户自助更新 settings（仅允许更新 settings 字段）"""
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您没有关联的租户")

    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")

    try:
        parsed = json.loads(body.settings) if isinstance(body.settings, str) else body.settings
        existing = _safe_json_loads(tenant.settings)
        existing.update(parsed)
        brand = existing.get("brand")
        if isinstance(brand, dict) and isinstance(brand.get("site_content"), dict):
            from app.services.jtbd_site_service import apply_jtbd_site_pass
            from app.services.site_content_bridge import sync_site_content_to_brand
            site_content = apply_jtbd_site_pass(brand["site_content"])
            brand["site_content"] = site_content
            existing["brand"] = sync_site_content_to_brand(brand, site_content)
        tenant.settings = json.dumps(existing, ensure_ascii=False)
        tenant.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(tenant)
        return success_response(data={"settings": parsed}, message="租户设置已更新")
    except (json.JSONDecodeError, TypeError) as e:
        return error_response(400, f"JSON 格式错误: {str(e)}")


class SiteAiGenerateRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=80)
    auto_save: bool = False
    product_images: list[str] = Field(default_factory=list)
    location_hint: str | None = Field(
        None,
        max_length=120,
        description="产地/产业带，如「河北廊坊大城县」",
    )
    run_product_research: bool = Field(
        False,
        description="建站前联网调研产品规格（AnySearch，失败不阻断；默认关闭以加快首屏）",
    )
    skip_i18n_ai: bool = Field(
        False,
        description="跳过建站时的多语种 AI 翻译（模板 i18n 仍补全；后台可再跑全量翻译）",
    )


def _persist_tenant_site_content(
    db: Session,
    tenant: Tenant,
    site_content: dict[str, Any],
    product_name: str,
) -> None:
    """执行 persist_tenant_site_content 相关逻辑处理。
    
    :param db: 数据库会话
    :param tenant: 租户对象
    :param site_content: 参数 site_content
    :param product_name: 参数 product_name
    :return: 返回处理结果。
    """
    from app.services.tenant_site_persistence import persist_tenant_site_content
    persist_tenant_site_content(db, tenant, site_content, product_name)


@router.post("/self/site-generate")
async def generate_tenant_site_content(
    body: SiteAiGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """租户输入产品名，Hermes 智能建站（设计技能约束）。"""
    from app.core.deps.tenant_quota import consume_tenant_tokens
    from app.services.hermes.site_build_workflow import run_ai_site_builder_v1
    from app.services.tenant_site_persistence import persist_tenant_site_content
    from app.services.token_service import InsufficientTokenError
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    tenant_id: Optional[str] = None
    company_name = ""
    tenant: Tenant | None = None
    if link:
        tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
        if tenant:
            tenant_id = str(tenant.id)
            company_name = tenant.name or ""

    product_name = body.product_name.strip()
    use_ai = True
    quota_note = ""
    product_profile: dict | None = None
    if tenant:
        from app.services.tenant_product_profile_service import build_and_persist_product_profile
        product_profile = build_and_persist_product_profile(
            db,
            tenant,
            product_hint=product_name,
            location_hint=body.location_hint,
            run_web_research=body.run_product_research,
        )
        if product_profile.get("primary_product"):
            product_name = str(product_profile["primary_product"]).strip() or product_name

    if tenant_id:
        try:
            consume_tenant_tokens(db, tenant_id, 50, "site_ai_generate")
        except InsufficientTokenError as e:
            use_ai = False
            quota_note = str(e)

    try:
        result = await run_ai_site_builder_v1(
            db,
            tenant_id=tenant_id or "anonymous",
            product_name=product_name,
            company_name=company_name,
            auto_save=bool(body.auto_save and tenant),
            use_ai=use_ai,
            persist_fn=persist_tenant_site_content if tenant else None,
            product_images=body.product_images or None,
            skip_i18n_ai=bool(body.skip_i18n_ai),
        )
    except ValueError as e:
        return error_response(400, str(e))

    msg = result.get("reply") or "网站内容已生成"
    if result.get("source") == "template" and quota_note:
        msg = f"AI 额度不足，已使用智能模板生成（{quota_note}）"

    saved = bool(result.get("saved"))
    return success_response(
        data={
            "site_content": result["site_content"],
            "source": result.get("source"),
            "saved": saved,
            "design_skills_applied": result.get("design_skills_applied"),
            "hermes_plugin": "ai_site_builder",
            "product_profile": product_profile,
            "l_pro_publish_gate": result.get("l_pro_publish_gate"),
        },
        message=msg,
    )


@router.get("/self/onboarding-status")
def get_self_onboarding_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """新手指引状态：是否已建站、是否完成向导。"""
    from app.services.onboarding_progress_service import _tenant_has_site
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return success_response(data={
            "has_tenant": False,
            "site_built": False,
            "wizard_completed": False,
            "primary_product": "",
            "company_name": "",
            "tenant_domain": "",
        })

    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")

    settings = _safe_json_loads(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    from app.services.onboarding_autopilot_service import get_autopilot_summary
    from app.services.onboarding_autopilot_job import get_autopilot_job
    from app.services.onboarding_chain_service import build_chain_status
    from app.services.tenant_product_context import resolve_tenant_product_hint
    chain = build_chain_status(tenant, db)
    autopilot = get_autopilot_summary(tenant)
    autopilot_job = get_autopilot_job(tenant)
    return success_response(data={
        "has_tenant": True,
        "site_built": _tenant_has_site(tenant),
        "wizard_completed": bool(onboarding.get("wizard_completed")),
        "autopilot_completed": bool(onboarding.get("autopilot_completed")),
        "primary_product": resolve_tenant_product_hint(tenant) or "",
        "location_hint": onboarding.get("location_hint") or "",
        "product_profile_ready": bool(
            isinstance(onboarding.get("product_profile"), dict)
            and onboarding["product_profile"].get("ready_for_outreach")
        ),
        "company_name": tenant.name or "",
        "tenant_domain": tenant.domain or "",
        "autopilot": autopilot,
        "autopilot_job": autopilot_job,
        **chain,
    })


@router.get("/self/product-profile")
def get_self_product_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    refresh: bool = Query(False, description="强制重建产品画像"),
    run_web_research: bool = Query(False, description="重建时是否联网调研"),
):
    """租户产品画像 — 开发信/建站共用（产品库优先）。"""
    from app.services.tenant_product_profile_service import (
        build_and_persist_product_profile,
        get_tenant_product_profile,
    )
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您没有关联的租户")
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")
    if refresh:
        profile = build_and_persist_product_profile(
            db, tenant, run_web_research=run_web_research
        )
    else:
        profile = get_tenant_product_profile(db, str(tenant.id))
    return success_response(data=profile)


class OnboardingWizardCompleteRequest(BaseModel):
    skip_remaining: bool = False


@router.post("/self/onboarding-wizard/complete")
def complete_onboarding_wizard(
    body: OnboardingWizardCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记新手指引已完成。"""
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您没有关联的租户")

    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")

    settings = _safe_json_loads(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    onboarding["wizard_completed"] = True
    onboarding["wizard_completed_at"] = datetime.now(timezone.utc).isoformat()
    if body.skip_remaining:
        onboarding["wizard_skipped"] = True
    settings["onboarding"] = onboarding
    tenant.settings = json.dumps(settings, ensure_ascii=False)
    tenant.updated_at = datetime.now(timezone.utc)
    db.commit()
    return success_response(message="新手指引已完成")


class OnboardingWangcaiPreviewRequest(BaseModel):
    message: str | None = Field(None, max_length=800)


@router.post("/self/onboarding-chain/wangcai-preview")
def onboarding_wangcai_preview(
    body: OnboardingWangcaiPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """向导 Step：旺财 Trade Q&A 预览（与公开站同源逻辑）。"""
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您没有关联的租户")
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")

    from app.services.onboarding_chain_service import run_wangcai_preview
    data = run_wangcai_preview(db, tenant, message=body.message)
    return success_response(data=data, message="旺财预览完成")


@router.post("/self/onboarding-chain/first-publish")
def onboarding_first_publish(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """向导 Step：生成首篇发布草稿并入队（需平台绑定后 Worker 执行）。"""
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您没有关联的租户")
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")

    from app.services.onboarding_chain_service import create_first_publish
    data = create_first_publish(db, tenant, current_user)
    msg = "首篇已入队" if data.get("task_id") else (data.get("note") or "首篇内容已创建")
    return success_response(data=data, message=msg)


class OnboardingImContactsRequest(BaseModel):
    whatsapp: str | None = Field(None, max_length=40)
    wechat: str | None = Field(None, max_length=80)
    telegram: str | None = Field(None, max_length=80)
    line: str | None = Field(None, max_length=80)
    phone: str | None = Field(None, max_length=40)
    email: str | None = Field(None, max_length=120)
    mark_done: bool = True


@router.get("/self/onboarding-chain/im-contacts")
def onboarding_im_contacts_get(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """向导：读取即时通讯联系方式（官网挂件用，非旺财 Trade Q&A）。"""
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您没有关联的租户")
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")

    from app.services.onboarding_im_contacts_service import get_im_contacts_status
    return success_response(data=get_im_contacts_status(tenant))


@router.post("/self/onboarding-chain/im-contacts")
def onboarding_im_contacts_save(
    body: OnboardingImContactsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """向导：保存 WhatsApp/微信等 IM → 写入官网 contact 页。"""
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您没有关联的租户")
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")

    from app.services.onboarding_im_contacts_service import save_im_contacts
    data = save_im_contacts(db, tenant, body.model_dump(), mark_done=body.mark_done)
    if not data.get("ok"):
        return error_response(400, data.get("error") or "保存失败")
    return success_response(data=data, message="联系方式已写入官网，客户挂件可一键联系")


class OnboardingPlatformBindRequest(BaseModel):
    platform_id: str | None = None
    platform_name: str | None = Field(None, max_length=80)
    username: str | None = Field(None, max_length=120)
    password: str | None = Field(None, max_length=200)
    cookie: str | None = None
    region: str | None = Field(None, max_length=20)
    configs: dict | None = None
    token_data: dict | None = None


@router.get("/self/onboarding-chain/first-platform")
def onboarding_first_platform(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """向导：首个待绑定平台位（内嵌绑定，不跳转菜单）。"""
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您没有关联的租户")
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")

    from app.services.onboarding_platform_service import get_first_platform_slot
    return success_response(data=get_first_platform_slot(db, tenant))


@router.post("/self/onboarding-chain/bind-platform")
def onboarding_bind_platform(
    body: OnboardingPlatformBindRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """向导内绑定第一个平台（OAuth Token / Cookie）。"""
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您没有关联的租户")
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")

    from app.services.onboarding_platform_service import bind_first_platform
    payload = body.model_dump(exclude_none=True)
    data = bind_first_platform(db, tenant, payload=payload)
    if not data.get("ok"):
        return error_response(400, data.get("error") or "绑定失败")
    msg = "平台绑定成功"
    if data.get("queued_task_id"):
        msg = "平台绑定成功，首篇已自动入队"
    return success_response(data=data, message=msg)


class OnboardingAutopilotRequest(BaseModel):
    product_name: str | None = Field(None, max_length=80)
    product_images: list[str] = Field(default_factory=list)
    skip_hermes: bool = False


@router.post("/self/onboarding-autopilot/run")
async def onboarding_autopilot_run(
    body: OnboardingAutopilotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """一键开业：Hermes 建站 + 旺财蓝海 + 首篇草稿（Time-to-Value）。"""
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您没有关联的租户")
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")

    from app.services.onboarding_autopilot_service import run_onboarding_autopilot
    data = await run_onboarding_autopilot(
        db,
        tenant,
        current_user,
        product_name=body.product_name,
        product_images=body.product_images or None,
        skip_hermes=body.skip_hermes,
    )
    msg = data.get("headline") or ("一键开业完成" if data.get("ok") else "部分步骤未完成，请按向导补做")
    return success_response(data=data, message=msg)


class TenantAiScenarioUpdate(BaseModel):
    overrides: Dict[str, str] = Field(default_factory=dict)


def _tenant_for_user(db: Session, user: User, tenant_id: Optional[str] = None):
    """执行 tenant_for_user 相关逻辑处理。
    
    :param db: 数据库会话
    :param user: 用户对象
    :param tenant_id: 租户ID
    :return: 返回处理结果。
    """
    if user.role in ("admin", "super_admin"):
        if not tenant_id:
            return None, error_response(400, "请指定 tenant_id")
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return None, error_response(404, "租户不存在")
        return tenant, None

    link = db.query(UserTenant).filter(
        UserTenant.user_id == user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return None, error_response(403, "您没有关联的租户")
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return None, error_response(404, "租户不存在")
    return tenant, None


@router.get("/self/ai-scenarios")
def get_self_ai_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """租户查看平台默认 + 自身覆盖 + 生效模型。"""
    tenant, err = _tenant_for_user(db, current_user)
    if err:
        return err
    return success_response(data=build_tenant_scenario_payload(db, tenant))


@router.get("/self/ai-traffic-provider")
def get_self_ai_traffic_provider(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前租户首选大模型平台（充值时自选）。"""
    from app.services.ai_traffic_provider_service import (
        get_tenant_ai_traffic_provider,
        list_providers_for_client,
        provider_label,
    )
    tenant, err = _tenant_for_user(db, current_user)
    if err:
        return err
    pid = get_tenant_ai_traffic_provider(tenant)
    return success_response(
        data={
            "current_provider_id": pid,
            "current_provider_label": provider_label(pid) if pid else None,
            "providers": list_providers_for_client(),
        }
    )


@router.put("/self/ai-traffic-provider")
def update_self_ai_traffic_provider(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """保存首选大模型平台（不支付也可先选好）。"""
    from app.services.ai_traffic_provider_service import (
        resolve_provider_id,
        set_tenant_ai_traffic_provider,
        provider_label,
    )
    tenant, err = _tenant_for_user(db, current_user)
    if err:
        return err
    raw = body.get("provider_id") if isinstance(body, dict) else None
    try:
        pid = set_tenant_ai_traffic_provider(db, tenant, str(raw or ""))
    except ValueError as exc:
        return error_response(400, str(exc))
    db.commit()
    return success_response(
        data={"provider_id": pid, "provider_label": provider_label(pid)},
        message=f"已选择大模型平台：{provider_label(pid)}",
    )


@router.put("/self/ai-scenarios")
def update_self_ai_scenarios(
    body: TenantAiScenarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """租户覆盖部分场景的模型（空值表示清除覆盖）。"""
    tenant, err = _tenant_for_user(db, current_user)
    if err:
        return err
    saved = write_tenant_overrides(db, tenant, body.overrides)
    return success_response(
        data=build_tenant_scenario_payload(db, tenant),
        message=f"已保存 {len(saved)} 项租户场景覆盖",
    )


@router.get("/{tenant_id}/ai-scenarios")
def get_tenant_ai_scenarios(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /{tenant_id}/ai-scenarios 请求，获取相关资源。
    
    :param tenant_id: 租户ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "权限不足")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")
    return success_response(data=build_tenant_scenario_payload(db, tenant))


@router.put("/{tenant_id}/ai-scenarios")
def update_tenant_ai_scenarios(
    tenant_id: str,
    body: TenantAiScenarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PUT /{tenant_id}/ai-scenarios 请求，更新相关资源。
    
    :param tenant_id: 租户ID
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "权限不足")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")
    saved = write_tenant_overrides(db, tenant, body.overrides)
    return success_response(
        data=build_tenant_scenario_payload(db, tenant),
        message=f"已保存 {len(saved)} 项租户场景覆盖",
    )


# ==================== 公开接口 (无需认证) ====================


@router.get("/domain/{domain:path}")
def get_tenant_by_domain(
    domain: str,
    db: Session = Depends(get_db),
):
    """
    根据域名前缀查询租户公开信息（无需登录）。

    当访客访问 tenant.youding-saas.com 时，前端通过此接口加载
    该租户的品牌配置、主题色、产品分类展示列表。

    domain 参数为子域名前缀，例如:
      - customer1.youding-saas.com  传入 customer1
      - tenant.custom.com           传入 tenant.custom.com (完整域名)
    """
    from app.repositories.tenant_repository import TenantRepository
    repo = TenantRepository(db)
    # 先尝试子域名前缀查找
    tenant = repo.get_by_domain(domain)
    if not tenant:
        return error_response(404, "站点不存在")

    if not tenant.is_active:
        return error_response(404, "站点已停用")

    settings_dict = _safe_json_loads(tenant.settings)
    brand_data = settings_dict.get("brand", {})
    white_label = settings_dict.get("white_label", {})
    from app.services.site_content_bridge import enrich_brand_from_site_content
    brand_data = enrich_brand_from_site_content(
        brand_data if isinstance(brand_data, dict) else {}
    )
    # 从 brand 或 white_label 回退填充品牌信息
    brand_config = TenantBrandConfig(
        site_title=brand_data.get("site_title", white_label.get("brand_name", tenant.name)),
        logo_url=brand_data.get("logo_url", white_label.get("logo_url", "")),
        brand_colors={
            "primary": brand_data.get("brand_colors", {}).get(
                "primary", white_label.get("primary_color", "#1890ff")
            ),
            "secondary": brand_data.get("brand_colors", {}).get("secondary", "#6b7280"),
            "accent": brand_data.get("brand_colors", {}).get("accent", "#f59e0b"),
        },
        product_categories=brand_data.get("product_categories", []),
        company_name=brand_data.get("company_name", tenant.name),
        slogan=brand_data.get("slogan", ""),
        about_summary=brand_data.get("about_summary", ""),
        contact_phone=brand_data.get(
            "contact_phone",
            white_label.get("contact_phone", tenant.contact_phone or ""),
        ),
        contact_email=brand_data.get(
            "contact_email",
            white_label.get("contact_email", tenant.contact_email or ""),
        ),
        footer_text=brand_data.get(
            "footer_text",
            white_label.get("footer_text", ""),
        ),
        custom_css=brand_data.get(
            "custom_css",
            white_label.get("custom_css", ""),
        ),
        site_content=brand_data.get("site_content"),
    )
    plan_code = tenant.plan.code if tenant.plan else None
    return success_response(data=TenantPublicResponse(
        id=str(tenant.id),
        name=tenant.name,
        domain=tenant.domain,
        status=tenant.status,
        plan_code=plan_code,
        brand=brand_config,
        is_online=tenant.is_active and tenant.status in ("active", "trial"),
    ))


@router.post("/", response_model=APIResponse[TenantResponse])
def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建租户"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = TenantService(db)
    try:
        tenant = service.create_tenant(tenant_data)
        return success_response(
            data=TenantResponse.model_validate(tenant),
            message="租户创建成功",
        )
    except ValueError as e:
        return error_response(400, str(e))


@router.get("/plans", response_model=APIResponse[list[TenantPlanResponse]])
def get_tenant_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取套餐列表"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = TenantPlanService(db)
    plans = service.list_plans()
    return success_response(data=[TenantPlanResponse.model_validate(p) for p in plans])


@router.post("/plans", response_model=APIResponse[TenantPlanResponse])
def create_tenant_plan(
    plan_data: TenantPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建套餐"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")

    service = TenantPlanService(db)
    try:
        plan = service.create_plan(plan_data)
        return success_response(
            data=TenantPlanResponse.model_validate(plan),
            message="套餐创建成功",
        )
    except ValueError as e:
        return error_response(400, str(e))


@router.put("/plans/{plan_id}", response_model=APIResponse[TenantPlanResponse])
def update_tenant_plan(
    plan_id: str,
    plan_data: TenantPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新套餐"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")

    service = TenantPlanService(db)
    plan = service.update_plan(plan_id, plan_data)
    if not plan:
        return error_response(404, "套餐不存在")

    return success_response(
        data=TenantPlanResponse.model_validate(plan),
        message="套餐更新成功",
    )


class AddTenantDomainRequest(BaseModel):
    domain: str = Field(..., min_length=3, max_length=255)


@router.get("/domains")
def get_tenant_domains(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前租户域名列表（主域名与自定义域名）"""
    ut = db.query(UserTenant).filter(UserTenant.user_id == current_user.id, UserTenant.is_active.is_(True)).first()
    tenant = db.query(Tenant).filter(Tenant.id == ut.tenant_id).first() if ut else db.query(Tenant).first()
    primary = (tenant.domain if tenant else "") or "dev.local"
    raw = tenant.custom_domains if tenant else ""
    if isinstance(raw, str):
        try:
            custom_domains = json.loads(raw) if raw else []
        except Exception:
            custom_domains = [raw] if raw else []
    elif isinstance(raw, list):
        custom_domains = raw
    else:
        custom_domains = []
    domain_list = [{"id": d, "domain": d, "verifyStatus": "verified", "sslStatus": "active"} for d in custom_domains]
    return success_response(data={"primaryDomain": primary, "domains": domain_list})


@router.post("/domains")
def add_tenant_domain(
    body: AddTenantDomainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """为当前租户添加自定义域名"""
    ut = db.query(UserTenant).filter(UserTenant.user_id == current_user.id, UserTenant.is_active.is_(True)).first()
    tenant = db.query(Tenant).filter(Tenant.id == ut.tenant_id).first() if ut else db.query(Tenant).first()
    if not tenant:
        return error_response(404, "租户不存在")
    raw = tenant.custom_domains
    if isinstance(raw, str):
        try:
            cur = json.loads(raw) if raw else []
        except Exception:
            cur = [raw] if raw else []
    elif isinstance(raw, list):
        cur = list(raw)
    else:
        cur = []
    if body.domain not in cur:
        cur.append(body.domain)
        tenant.custom_domains = json.dumps(cur)
        db.commit()
    return success_response(message="域名已添加", data={"domain": body.domain})


@router.get("/{tenant_id}", response_model=APIResponse[TenantResponse])
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取租户详情"""
    if tenant_id in {"plans", "register", "current", "pricing", "invoices", "domains"}:
        return error_response(404, "接口不存在")

    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = TenantService(db)
    tenant = service.get_tenant(tenant_id)
    if not tenant:
        return error_response(404, "租户不存在")

    return success_response(data=TenantResponse.model_validate(tenant))


@router.put("/{tenant_id}", response_model=APIResponse[TenantResponse])
def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新租户"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = TenantService(db)
    try:
        tenant = service.update_tenant(tenant_id, tenant_data)
        if not tenant:
            return error_response(404, "租户不存在")
        return success_response(
            data=TenantResponse.model_validate(tenant),
            message="租户更新成功",
        )
    except ValueError as e:
        return error_response(400, str(e))


@router.delete("/{tenant_id}", response_model=APIResponse)
def delete_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除租户"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")

    service = TenantService(db)
    if not service.delete_tenant(tenant_id):
        return error_response(404, "租户不存在")

    return success_response(message="租户删除成功")


@router.get("/{tenant_id}/invoices", response_model=APIResponse[TenantInvoiceListResponse])
def get_tenant_invoices(
    tenant_id: str,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取租户账单"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = TenantService(db)
    items, total = service.list_invoices(tenant_id, page=page, page_size=page_size)
    return success_response(
        data=TenantInvoiceListResponse(
            items=[TenantInvoiceResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/{tenant_id}/invoices/{invoice_id}/pdf")
def download_tenant_invoice_pdf(
    tenant_id: str,
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """P1-08：下载账单 PDF。"""
    from fastapi.responses import Response
    from app.models.tenant import Tenant, TenantInvoice
    from app.services.invoice_pdf_service import build_invoice_pdf_bytes
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    inv = (
        db.query(TenantInvoice)
        .filter(TenantInvoice.id == invoice_id, TenantInvoice.tenant_id == tenant_id)
        .first()
    )
    if not inv:
        return error_response(404, "账单不存在")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    payload = {
        "id": str(inv.id),
        "tenant_id": str(inv.tenant_id),
        "amount": inv.amount,
        "status": inv.status,
        "due_at": inv.due_at.isoformat() if inv.due_at else "",
        "paid_at": inv.paid_at.isoformat() if inv.paid_at else "",
    }
    pdf = build_invoice_pdf_bytes(payload, tenant.name if tenant else "")
    filename = f"invoice-{invoice_id[:8]}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{tenant_id}/white-label", response_model=APIResponse[WhiteLabelConfig])
def get_white_label_config(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取白标品牌配置"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = TenantService(db)
    try:
        config = service.get_white_label_config(tenant_id)
        return success_response(data=config)
    except ValueError as e:
        return error_response(404, str(e))


@router.put("/{tenant_id}/white-label", response_model=APIResponse[WhiteLabelConfig])
def update_white_label_config(
    tenant_id: str,
    wl_data: WhiteLabelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新白标品牌配置"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = TenantService(db)
    try:
        config = service.update_white_label(tenant_id, wl_data)
        return success_response(data=config, message="白标配置已更新")
    except ValueError as e:
        return error_response(404, str(e))


@router.get("/register/catalog")
def get_register_catalog(db: Session = Depends(get_db)):
    """开户页：一次性开通项说明 + 可选平台列表（无需登录）。"""
    from app.services.tenant_onboarding_service import get_register_catalog as _catalog
    return success_response(data=_catalog(db))


@router.get("/self/external-accounts")
def get_self_external_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """租户：第三方注册/实名流程清单（按所选平台与存储分区过滤）。"""
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您没有关联的租户")

    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")

    settings_dict = _safe_json_loads(tenant.settings)
    onboarding = settings_dict.get("onboarding") if isinstance(settings_dict.get("onboarding"), dict) else {}
    platform_slots = onboarding.get("platforms") if isinstance(onboarding.get("platforms"), list) else []
    platform_names = [str(p.get("platform_name") or "") for p in platform_slots]
    storage = onboarding.get("storage") if isinstance(onboarding.get("storage"), dict) else {}
    from app.services.onboarding_external_accounts import (
        build_external_accounts,
        build_external_accounts_phases,
        get_register_external_preview,
    )
    accounts = build_external_accounts(
        tenant,
        platform_names=platform_names,
        storage_region=(storage.get("product_images") or {}).get("storage_region"),
    )
    return success_response(
        data={
            "preview": get_register_external_preview(),
            "accounts": accounts,
            "phases": build_external_accounts_phases(accounts),
        }
    )


def _resolve_register_client_ip(request: Request) -> str:
    """解析客户端真实 IP（兼容 x-forwarded-for）。"""
    client_ip = request.client.host if request.client else "unknown"
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        client_ip = fwd.split(",")[0].strip()
    return client_ip


def _create_register_entities(db: Session, body: TenantRegisterSchema, plan, now):
    """创建用户、租户、订阅与用户-租户关联，返回 (user, tenant, trial_end)。"""
    # 3. 创建用户 (role='tenant_admin')
    user = User(
        id=str(uuid.uuid4()),
        username=body.email.split("@")[0],
        email=body.email,
        display_name=body.admin_name,
        hashed_password=get_password_hash(body.password),
        role="tenant_admin",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.flush()
    # 4. 创建租户
    tenant_domain = body.company_name.lower().replace(
        r"\s+", "-").replace(r"[^a-z0-9-]", "")[:50]
    if not tenant_domain:
        tenant_domain = f"t-{uuid.uuid4().hex[:8]}"

    trial_end = now + timedelta(days=14)
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=body.company_name,
        contact_name=body.admin_name,
        contact_email=body.email,
        contact_phone=(body.contact_phone or "").strip() or None,
        domain=tenant_domain,
        plan_id=plan.id,
        status="trial",
        trial_ends_at=trial_end,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(tenant)
    db.flush()
    # 5. 创建订阅
    subscription = TenantSubscription(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        plan_id=plan.id,
        billing_cycle="monthly",
        amount=plan.price_monthly,
        status="active",
        started_at=now,
        created_at=now,
    )
    db.add(subscription)
    db.flush()
    # 6. 创建用户-租户关联
    user_tenant = UserTenant(
        id=str(uuid.uuid4()),
        user_id=user.id,
        tenant_id=tenant.id,
        role="tenant_admin",
        is_active=True,
        created_at=now,
    )
    db.add(user_tenant)
    db.flush()
    return user, tenant, trial_end


def _apply_register_extras(db, body, tenant, user, plan, trial_end, verification):
    """处理访客视频绑定、邀请码绑定、一站式开户与验证码核销，返回 (guest_bound, onboarding)。"""
    # 6a. 访客视频任务归属（多媒体工厂 guest_token）
    guest_bound = 0
    if body.guest_token and body.guest_token.strip():
        from app.services.media_guest_service import bind_guest_media_to_tenant
        guest_bound = bind_guest_media_to_tenant(db, body.guest_token.strip(), str(tenant.id))

    # 6b. 邀请码绑定（获客闭环）
    if body.referral_code and body.referral_code.strip():
        from app.services.referral_service import ReferralService
        referral_result = ReferralService(db).apply_referral(
            body.referral_code.strip().upper(),
            str(tenant.id),
        )
        if referral_result.get("success") and referral_result.get("extra_days"):
            extra = int(referral_result["extra_days"])
            tenant.trial_ends_at = (tenant.trial_ends_at or trial_end) + timedelta(days=extra)

    # 6c. 一站式开户：AI 场景 + 云存储路径 + 平台账号槽位 + Egress
    from app.services.tenant_onboarding_service import (
        consume_email_verification,
        provision_tenant_onboarding,
    )
    onboarding = provision_tenant_onboarding(
        db,
        tenant,
        user,
        plan,
        platform_names=body.platform_names,
        email_verified=True,
        primary_product=body.primary_product,
        location_hint=body.location_hint,
    )
    consume_email_verification(db, verification)
    return guest_bound, onboarding


def _run_register_autopilot(db, body, tenant, user):
    """开户后异步构建产品画像并调度 autopilot 任务。"""
    product_for_autopilot = (body.primary_product or "").strip()
    if not product_for_autopilot:
        return
    from app.services.tenant_product_profile_service import build_and_persist_product_profile
    try:
        build_and_persist_product_profile(
            db,
            tenant,
            product_hint=product_for_autopilot,
            location_hint=body.location_hint,
            run_web_research=True,
        )
    except Exception:
        pass
    from app.services.onboarding_autopilot_job import (
        schedule_autopilot_after_register,
        set_autopilot_job,
    )
    set_autopilot_job(
        db,
        str(tenant.id),
        {
            "status": "pending",
            "product": product_for_autopilot,
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    schedule_autopilot_after_register(
        tenant_id=str(tenant.id),
        user_id=str(user.id),
        product_name=product_for_autopilot,
    )


def _build_register_tokens(user) -> TokenResponse:
    """签发 access/refresh token 并组装 TokenResponse。"""
    from app.core.config import settings
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "scopes": [user.role]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_access_token(
        data={"sub": str(user.id), "scopes": ["refresh"]},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    token_data = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )
    return token_data


def _build_register_payload(token_data, onboarding, tenant, guest_bound) -> dict:
    """组装返回给前端的 payload 字典。"""
    payload = token_data.model_dump()
    payload["onboarding"] = onboarding
    payload["tenant_id"] = str(tenant.id)
    payload["tenant_domain"] = tenant.domain
    return payload


@router.post("/register", response_model=APIResponse[TokenResponse])
def register_tenant(
    body: TenantRegisterSchema,
    request: Request,
    db: Session = Depends(get_db),
):
    """客户自助注册 - 验证码 + 租户 + AI/存储/平台槽位一站式开通，自动登录"""
    # ── 限流：5 次/小时/IP ──
    client_ip = _resolve_register_client_ip(request)
    _check_register_rate(client_ip)
    from app.services.tenant_onboarding_service import (
        verify_register_email_code,
    )
    # 0. 邮箱验证码（与登录共用发码接口 POST /auth/send-email-code）
    verification = verify_register_email_code(db, body.email, body.email_code)
    if not verification:
        return error_response(400, "验证码无效或已过期，请重新获取")

    # 1. 检查邮箱是否已存在
    existing_user = db.query(User).filter(User.email == body.email).first()
    if existing_user:
        return error_response(409, "该邮箱已被注册")

    # 2. 查找套餐
    plan_repo = TenantPlanRepository(db)
    plan = plan_repo.get_by_code(body.plan_code)
    if not plan:
        return error_response(400, f"套餐 '{body.plan_code}' 不存在")

    now = datetime.now(timezone.utc)
    user, tenant, trial_end = _create_register_entities(db, body, plan, now)
    guest_bound, onboarding = _apply_register_extras(db, body, tenant, user, plan, trial_end, verification)
    db.commit()
    _run_register_autopilot(db, body, tenant, user)
    token_data = _build_register_tokens(user)
    payload = _build_register_payload(token_data, onboarding, tenant, guest_bound)
    return success_response(
        data=payload,
        message=(
            "开户成功：AI、存储与平台账号位已预置"
            + (f"，已关联 {guest_bound} 条访客视频" if guest_bound else "")
        ),
    )
