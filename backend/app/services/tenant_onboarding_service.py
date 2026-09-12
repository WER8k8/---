"""租户开户一站式编排：验证码、AI 场景、云存储路径、平台账号槽位。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Platform, PlatformAccount
from app.models.tenant import Tenant, TenantPlan
from app.models.user import EmailVerification, User
from app.services.egress_quota_service import auto_assign_slots_for_tenant, get_egress_quota
from app.services.platform_catalog import PILOT_NAMES
from app.services.tenant_scenario_service import TENANT_ALLOWED_SCENARIOS

# 开户默认预置平台（可在注册页勾选增减）
DEFAULT_REGISTER_PLATFORM_NAMES = sorted(PILOT_NAMES)


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def _safe_settings(raw: str | None) -> dict[str, Any]:
    """_safe_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def verify_register_email_code(db: Session, email: str, code: str) -> EmailVerification | None:
    """verify_register_email_code。

    参数说明：
    :param db: 参数 db
    :param email: 参数 email
    :param code: 参数 code
    :return: 返回处理结果。
    """
    email = (email or "").strip().lower()
    code = (code or "").strip()
    if not email or not code:
        return None
    import hashlib
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    return (
        db.query(EmailVerification)
        .filter(
            EmailVerification.email == email,
            EmailVerification.code == code_hash,
            EmailVerification.used.is_(False),
            EmailVerification.expires_at > _utcnow(),
        )
        .first()
    )


def consume_email_verification(db: Session, row: EmailVerification) -> None:
    """consume_email_verification。

    参数说明：
    :param db: 参数 db
    :param row: 参数 row
    :return: 返回处理结果。
    """
    row.used = True
    db.add(row)


def _plan_feature_flags(plan: TenantPlan | None) -> dict[str, bool]:
    """_plan_feature_flags。

    参数说明：
    :param plan: 参数 plan
    :return: 返回处理结果。
    """
    raw: list[str] = []
    if plan and plan.features:
        try:
            parsed = json.loads(plan.features)
            raw = parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            raw = []
    joined = " ".join(str(x) for x in raw).lower()
    return {
        "seo": "seo" in joined,
        "ai_content": "ai" in joined or "内容" in joined,
        "video": "视频" in joined or "video" in joined,
        "globalization": "全球" in joined or "多语言" in joined,
        "inquiry": "询盘" in joined,
    }


def _platform_slots(db: Session, selected_names: list[str] | None) -> list[dict[str, Any]]:
    """仅对注册时显式勾选的平台建槽位；未选则留空，由客户在多平台分发页自选/自填。"""
    if not selected_names:
        return []
    slots: list[dict[str, Any]] = []
    for name in selected_names:
        plat = db.query(Platform).filter(Platform.name == name).first()
        if not plat:
            continue
        slots.append(
            {
                "platform_id": str(plat.id),
                "platform_name": plat.name,
                "platform_type": plat.platform_type,
                "region": plat.region or "cn",
                "content_type": plat.content_type or "article",
                "status": "pending_connect",
                "login_status": "logged_out",
                "connect_hint": "管理后台 → SEO 矩阵 → 平台账号 → 绑定授权",
                "admin_path": "/client/seo-publish",
            }
        )
    return slots


def _lenslink_storage_status() -> dict[str, Any]:
    """_lenslink_storage_status。
    :return: 返回处理结果。
    """
    try:
        from app.services.media_lenslink_service import lenslink_configured
        if lenslink_configured():
            return {
                "status": "platform_configured",
                "enabled": True,
                "note": "平台已配置棱束链灾备，渲染完成后自动备份",
            }
    except Exception:
        pass
    return {
        "status": "optional_backup",
        "enabled": False,
        "note": "可选：运营配置 MEDIA_LENSLINK_* 后自动灾备",
    }


def _infer_storage_region(tenant: Tenant) -> str:
    """_infer_storage_region。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    ts = _safe_settings(tenant.settings)
    region = ts.get("storage_region")
    if region in ("cn", "global"):
        return str(region)
    flags = _plan_feature_flags(tenant.plan)
    if flags.get("globalization"):
        return "global"
    return "cn"


def _storage_provision(tenant: Tenant) -> dict[str, Any]:
    """_storage_provision。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    tid = str(tenant.id)
    return {
        "cuplayer": {
            "status": "awaiting_tenant_credentials",
            "note": "请在「设置 → 视频云存储」填写酷播 writetoken（开户已预留分类目录位）",
            "cataid_suggestion": 1,
            "title_prefix": tenant.name[:20],
        },
        "r2": {
            "status": "awaiting_platform_credentials",
            "object_prefix": f"tenants/{tid}/",
            "note": "平台 R2 由运营配置；您的视频将自动写入该前缀",
        },
        "minio": {
            "status": "shared_platform_bucket",
            "object_prefix": f"tenants/{tid}/uploads/",
            "note": "站内附件与开发资源，与视频 CDN 分离",
        },
        "product_images": {
            "cn": {
                "backend": "qiniu",
                "object_prefix": f"tenants/{tid}/images/",
                "note": "国内租户产品图走七牛；未配 QINIU_* 时暂存本地",
            },
            "global": {
                "backend": "r2",
                "object_prefix": f"tenants/{tid}/images/",
                "note": "出海/国际化租户产品图走 Cloudflare R2",
            },
            "storage_region": _infer_storage_region(tenant),
        },
        "lenslink": _lenslink_storage_status(),
    }


def _ai_provision(db: Session, tenant: Tenant, plan: TenantPlan | None) -> dict[str, Any]:
    """_ai_provision。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param plan: 参数 plan
    :return: 返回处理结果。
    """
    flags = _plan_feature_flags(plan)
    enabled = list(TENANT_ALLOWED_SCENARIOS) if flags.get("ai_content") or flags.get("video") else [
        "inference",
        "article",
    ]
    if flags.get("video"):
        enabled = list(TENANT_ALLOWED_SCENARIOS)

    settings = _safe_settings(tenant.settings)
    settings["onboarding_ai"] = {
        "enabled_scenarios": enabled,
        "quota_monthly": int(plan.max_ai_quota if plan else 0),
        "note": "已开通场景；模型 API Key 使用平台统一配置，租户可在「场景模型」覆盖",
    }
    tenant.settings = json.dumps(settings, ensure_ascii=False)
    db.add(tenant)
    return settings["onboarding_ai"]


def create_platform_account_stubs(
    db: Session,
    tenant: Tenant,
    platform_slots: list[dict[str, Any]],
) -> int:
    """为租户预置 platform_accounts 行（待 OAuth/Cookie 绑定）。"""
    tid = str(tenant.id)
    created = 0
    for slot in platform_slots:
        pid = slot.get("platform_id")
        if not pid:
            continue
        exists = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.tenant_id == tid,
                PlatformAccount.platform_id == str(pid),
            )
            .first()
        )
        if exists:
            continue
        plat = db.query(Platform).filter(Platform.id == pid).first()
        label = (plat.name if plat else slot.get("platform_name")) or "平台"
        db.add(
            PlatformAccount(
                id=str(uuid.uuid4()),
                tenant_id=tid,
                platform_id=str(pid),
                account_name=f"{tenant.name[:24]}-{label}",
                login_status="logged_out",
                is_active=True,
            )
        )
        created += 1
    if created:
        db.flush()
    return created


def provision_tenant_onboarding(
    db: Session,
    tenant: Tenant,
    user: User,
    plan: TenantPlan | None,
    *,
    platform_names: list[str] | None = None,
    email_verified: bool = True,
    primary_product: str | None = None,
    location_hint: str | None = None,
) -> dict[str, Any]:
    """注册成功后一次性写入租户配置（不需客户稍后再开开关）。"""
    platform_slots = _platform_slots(db, platform_names)
    create_platform_account_stubs(db, tenant, platform_slots)
    storage = _storage_provision(tenant)
    ai_block = _ai_provision(db, tenant, plan)
    egress_quota = get_egress_quota(tenant, plan)
    egress_assigned = auto_assign_slots_for_tenant(db, tenant)
    brand_seed = {
        "site_title": tenant.name,
        "company_name": tenant.name,
        "contact_email": tenant.contact_email or user.email,
        "product_categories": [],
    }
    from app.services.onboarding_external_accounts import (
        build_external_accounts,
        build_external_accounts_phases,
    )
    platform_names = [p.get("platform_name") or "" for p in platform_slots]
    external_accounts = build_external_accounts(
        tenant,
        platform_names=platform_names,
        storage_region=storage.get("product_images", {}).get("storage_region"),
    )
    external_account_phases = build_external_accounts_phases(external_accounts)
    onboarding = {
        "version": 1,
        "provisioned_at": _utcnow().isoformat(),
        "email_verified": email_verified,
        "admin_user_id": str(user.id),
        "primary_product": (primary_product or "").strip(),
        "location_hint": (location_hint or "").strip(),
        "site_built": False,
        "wizard_completed": False,
        "ai": ai_block,
        "storage": storage,
        "platforms": platform_slots,
        "egress": {
            "quota": egress_quota,
            "assigned": egress_assigned,
        },
        "media_factory": {
            "guest_token_supported": True,
            "auto_tenant_video_site": True,
            "publish_traffic_enabled": True,
        },
        "brand_seed": brand_seed,
        "external_accounts": external_accounts,
        "external_account_phases": external_account_phases,
        "checklist": _build_checklist(
            platform_slots, storage, ai_block, egress_assigned, external_accounts
        ),
    }
    settings = _safe_settings(tenant.settings)
    settings["onboarding"] = onboarding
    settings["brand"] = {**settings.get("brand", {}), **brand_seed}
    tenant.settings = json.dumps(settings, ensure_ascii=False)
    db.add(tenant)
    db.flush()
    from app.services.tenant_aitoearn_slot_service import auto_assign_aitoearn_slot_for_tenant
    slot_result = auto_assign_aitoearn_slot_for_tenant(db, tenant)
    onboarding["aitoearn_slot"] = slot_result
    return onboarding


def _build_checklist(
    platforms: list[dict[str, Any]],
    storage: dict[str, Any],
    ai: dict[str, Any],
    egress_assigned: int,
    external_accounts: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """_build_checklist。

    参数说明：
    :param platforms: 参数 platforms
    :param storage: 参数 storage
    :param ai: 参数 ai
    :param egress_assigned: 参数 egress_assigned
    :param external_accounts: 参数 external_accounts
    :return: 返回处理结果。
    """
    items = [
        {
            "key": "email",
            "title": "邮箱验证",
            "status": "done",
            "detail": "开户验证码已通过",
        },
        {
            "key": "site",
            "title": "做出公司官网",
            "status": "pending",
            "detail": "填主营产品，点一键开业，系统自动生成网站",
            "route": "/client/onboarding",
            "phase": "开张",
        },
        {
            "key": "ai",
            "title": "智能写文案",
            "status": "done",
            "detail": f"开户已开通，可写 {len(ai.get('enabled_scenarios', []))} 类文案",
            "phase": "开张",
        },
        {
            "key": "product_images",
            "title": "产品图片空间",
            "status": "done",
            "detail": storage.get("product_images", {}).get("cn", {}).get("note", "国内七牛 / 海外 R2，平台代开"),
            "route": "/admin/file-manager",
            "phase": "开张",
        },
        {
            "key": "storage",
            "title": "视频云存储（酷播）",
            "status": "partial",
            "detail": "发长视频前：您需在酷播官网注册实名，并在设置里填 API 密钥",
            "route": "/client/settings",
            "phase": "让人看见",
        },
        {
            "key": "external_accounts",
            "title": "第三方账号准备",
            "status": "partial",
            "detail": "查看开户清单：哪些平台代开、哪些需您注册实名",
            "route": "/client/onboarding#external-accounts",
            "phase": "让人看见",
        },
        {
            "key": "egress",
            "title": "海外发布网络",
            "status": "done" if egress_assigned else "pending",
            "detail": f"已分配 {egress_assigned} 条线路，国外平台发布更稳",
            "route": "/client/egress",
            "phase": "让人看见",
        },
    ]
    pending_platforms = sum(1 for p in platforms if p.get("status") == "pending_connect")
    items.append(
        {
            "key": "platforms",
            "title": "绑定抖音等平台",
            "status": "pending" if pending_platforms else "done",
            "detail": f"已留 {len(platforms)} 个位置，登录绑定后才能真发出去",
            "route": "/client/distribute",
            "phase": "让人看见",
        },
    )
    from app.services.onboarding_progress_service import EXTRA_CHECKLIST_TEMPLATES, SALES_CHANNEL_SUBSTEPS
    for tpl in EXTRA_CHECKLIST_TEMPLATES:
        items.append({**tpl, "status": "pending"})
    for tpl in SALES_CHANNEL_SUBSTEPS:
        items.append(
            {
                **tpl,
                "status": "pending",
                "framework_step": 5,
                "substep_id": tpl["id"],
            }
        )
    return items


def backfill_tenant_platform_stubs(db: Session, *, dry_run: bool = False) -> dict[str, int]:
    """为历史租户补全 platform_accounts 占位（按 onboarding 或默认平台列表）。"""
    tenants = db.query(Tenant).all()
    tenants_touched = 0
    accounts_created = 0
    for tenant in tenants:
        settings = _safe_settings(tenant.settings)
        onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
        slots = onboarding.get("platforms") if isinstance(onboarding, dict) else None
        if not slots:
            slots = _platform_slots(db, None)
        if dry_run:
            for slot in slots:
                pid = slot.get("platform_id")
                if not pid:
                    continue
                exists = (
                    db.query(PlatformAccount)
                    .filter(
                        PlatformAccount.tenant_id == str(tenant.id),
                        PlatformAccount.platform_id == str(pid),
                    )
                    .first()
                )
                if not exists:
                    accounts_created += 1
            if slots:
                tenants_touched += 1
            continue
        created = create_platform_account_stubs(db, tenant, slots)
        if created:
            tenants_touched += 1
            accounts_created += created
    if not dry_run:
        db.commit()
    return {
        "tenants_scanned": len(tenants),
        "tenants_updated": tenants_touched,
        "accounts_created": accounts_created,
        "dry_run": dry_run,
    }


def get_register_catalog(db: Session) -> dict[str, Any]:
    """注册页展示：可选平台、说明。"""
    from app.services.onboarding_external_accounts import get_register_external_preview
    from app.services.trade_platform_meta import enrich_platform_row, group_platforms_for_register
    rows = db.query(Platform).filter(Platform.is_active.is_(True)).order_by(Platform.region, Platform.name).all()
    if not rows:
        from app.services.platform_catalog import all_catalog_rows
        flat = [
            enrich_platform_row(n, reg, ct)
            for n, _pt, reg, ct in all_catalog_rows()
        ]
    else:
        flat = [
            enrich_platform_row(p.name, p.region or "cn", p.content_type or "article", str(p.id))
            for p in rows
        ]
    return {
        "platforms": flat,
        "platform_groups": group_platforms_for_register(flat),
        "bundled_services": [
            "邮箱验证码开户（优丁账号）",
            "产品图片空间：国内七牛 / 海外 R2（平台代注册，您无需开云账号）",
            "AI 大模型场景（文章/视频脚本）",
            "视频点播路径（酷播 — 发视频前您需自备酷播账号）",
            "SEO 矩阵平台槽位（抖音/微信/YouTube 等需您注册并绑定）",
            "多媒体工厂 + 官网视频引流",
            "官网 IM 联系 + Trade Q&A 智能顾问",
        ],
        "external_accounts_preview": get_register_external_preview(),
        "im_tools_recommended": ["WhatsApp", "WeChat", "Telegram", "LINE"],
    }
