# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SaaS 客户管理后台 - 仪表盘与品牌接口"""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.inquiry import Inquiry
from app.models.product import Product
from app.models.tenant import Tenant, TenantPlan, UserTenant
from app.models.user import User
from app.schemas.tenant import TenantBrandConfig
from app.services.client_today_service import build_today_payload
from app.services.finance_honesty import apply_real_inquiry_filters, count_raw_inquiries, count_real_inquiries
from app.services.onboarding_autopilot_service import get_autopilot_summary
from app.services.onboarding_chain_service import resolve_client_site_url
from app.services.traffic_analytics_service import TrafficAnalyticsService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["SaaS客户管理后台"]

router = APIRouter(prefix="/client", tags=["SaaS客户管理后台"])


def _count_publish_in_progress(db: Session, tenant_id: str) -> int:
    """
    处理 _count_publish_in_progress 相关业务逻辑。

    :param db: 入参 (Session)。
    :param tenant_id: 入参 (str)。

    :return: 返回 int 类型的结果。
    """
    try:
        from app.models.content import PlatformAccount, PublishTask
        return (
            db.query(PublishTask)
            .join(PlatformAccount, PublishTask.account_id == PlatformAccount.id)
            .filter(
                PlatformAccount.tenant_id == tenant_id,
                PublishTask.status.in_(("pending", "processing")),
            )
            .count()
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("查询发布任务计数失败: %s", e)
        return 0


def _domain_status(tenant: Tenant) -> dict:
    """
    处理 _domain_status 相关业务逻辑。

    :param tenant: 入参 (Tenant)。

    :return: 返回 dict 类型的结果。
    """
    custom: list = []
    if tenant.custom_domains:
        try:
            parsed = json.loads(tenant.custom_domains)
            if isinstance(parsed, list):
                custom = [str(x) for x in parsed if x]
        except (json.JSONDecodeError, TypeError):
            custom = []
    primary = custom[0] if custom else None
    return {
        "subdomain": tenant.domain,
        "has_custom_domain": bool(custom),
        "primary_custom": primary,
        "label": primary or f"{tenant.domain}.youding-saas.com",
    }


def _resolve_tenant(db: Session, user: User) -> tuple:
    """根据当前用户解析其所属租户。

    Returns:
        (tenant, user_tenant_link, error_response_or_None)
    """
    link = db.query(UserTenant).filter(
        UserTenant.user_id == user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return None, None, error_response(403, "未关联到任何租户")

    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return None, None, error_response(404, "租户不存在")

    return tenant, link, None


@router.get("/dashboard")
def get_client_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取客户工作台数据"""
    tenant, link, err = _resolve_tenant(db, current_user)
    if err:
        return err

    tid = str(tenant.id)
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    inq_base = apply_real_inquiry_filters(
        db.query(Inquiry).filter(Inquiry.tenant_id == tid)
    )
    today_inquiries = count_real_inquiries(
        db, tenant_id=tid, today_start=today_start
    )
    pending_inquiries = count_real_inquiries(db, tenant_id=tid, status="pending")
    raw_pending = count_raw_inquiries(db, tenant_id=tid, status="pending")
    total_products = db.query(Product).filter(Product.is_active).count()
    recent = inq_base.order_by(Inquiry.created_at.desc()).limit(5).all()
    traffic_7d: dict = {}
    try:
        traffic_board = TrafficAnalyticsService(db).build_board(
            period="7d", tenant_id=tid, scope="tenant"
        )
        traffic_7d = traffic_board.get("summary") or {}
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("获取流量分析数据失败，使用空数据: %s", e)
        traffic_7d = {}

    ai_quota = _resolve_ai_quota(tenant)
    brand = _resolve_brand(tenant)
    publish_in_progress = _count_publish_in_progress(db, tid)
    domain_status = _domain_status(tenant)
    today = build_today_payload(
        db=db,
        tenant=tenant,
        pending_inquiries=pending_inquiries,
        publish_in_progress=publish_in_progress,
    )
    autopilot = get_autopilot_summary(tenant)
    journey_health = today.get("journey_health") or {}
    return success_response(data={
        "tenant_id": str(tenant.id),
        "brand": brand,
        "today_one_thing": today["today_one_thing"],
        "today_queue": today["today_queue"],
        "blue_ocean_hint": today["blue_ocean_hint"],
        "journey_health": journey_health,
        "autopilot": autopilot,
        "autopilot_headline": (autopilot or {}).get("headline"),
        "stats": _build_dashboard_stats(
            traffic_7d, today_inquiries, pending_inquiries, total_products
        ),
        "traffic_7d": traffic_7d,
        "plan_name": ai_quota["plan_name"],
        "plan_expiry": ai_quota["plan_expiry"],
        "tenant_status": tenant.status,
        "ai_quota_used": tenant.ai_quota_used or 0,
        "ai_quota_total": ai_quota["ai_quota_total"],
        "ai_traffic_provider_id": ai_quota["ai_traffic_provider_id"],
        "ai_traffic_provider_label": ai_quota["ai_traffic_provider_label"],
        "site_url": resolve_client_site_url(tenant),
        "publish_in_progress": publish_in_progress,
        "domain_status": domain_status,
        "recent_inquiries": [
            {"id": str(i.id), "name": i.name, "message": i.message,
             "time": i.created_at.strftime("%m-%d %H:%M") if i.created_at else "",
             "status": i.status}
            for i in recent
        ],
        "data_honesty": {
            "excluded_inquiries": max(0, raw_pending - pending_inquiries),
            "raw_pending_inquiries": raw_pending,
            "note": "已排除本地演示/测试询盘，未上线站点不会产生真实询盘。",
        },
    })


def _resolve_ai_quota(tenant: Tenant) -> dict:
    """解析租户的套餐、配额与 AI 流量通道信息。

    :param tenant: 租户对象。
    :return: 包含 plan_name/plan_expiry/ai_quota_total/ai_traffic_provider_id/ai_traffic_provider_label 的字典。
    """
    from app.services.ai_traffic_provider_service import (
        get_tenant_ai_traffic_provider,
        provider_label,
    )
    plan_name = tenant.plan.name if tenant.plan else "免费版"
    trial_end = tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None
    ai_quota_total = tenant.plan.max_ai_quota if tenant.plan else 0
    ai_provider_id = get_tenant_ai_traffic_provider(tenant)
    return {
        "plan_name": plan_name,
        "plan_expiry": trial_end,
        "ai_quota_total": ai_quota_total,
        "ai_traffic_provider_id": ai_provider_id,
        "ai_traffic_provider_label": provider_label(ai_provider_id) if ai_provider_id else None,
    }


def _resolve_brand(tenant: Tenant) -> dict:
    """解析租户品牌配置，缺省回退到租户名称。

    :param tenant: 租户对象。
    :return: 品牌配置字典。
    """
    brand = {"company_name": tenant.name, "slogan": ""}
    if tenant.settings:
        try:
            settings_dict = json.loads(tenant.settings)
            brand_data = settings_dict.get("brand", {})
            if brand_data:
                brand = brand_data
        except (json.JSONDecodeError, TypeError):
            pass
    return brand


def _build_dashboard_stats(
    traffic_7d: dict,
    today_inquiries: int,
    pending_inquiries: int,
    total_products: int,
) -> dict:
    """构建仪表盘统计指标字典。

    :param traffic_7d: 近 7 日流量汇总。
    :param today_inquiries: 今日真实询盘数。
    :param pending_inquiries: 待处理询盘数。
    :param total_products: 上架产品数。
    :return: 统计指标字典。
    """
    return {
        "today_inquiries": today_inquiries,
        "pending_inquiries": pending_inquiries,
        "total_products": total_products,
        "keyword_count": 0,
        "visitors_7d": traffic_7d.get("unique_visitors", 0),
        "page_views_7d": traffic_7d.get("page_views", 0),
        "clicks_7d": traffic_7d.get("total_clicks", 0),
        "inquiries_7d": traffic_7d.get("inquiries", 0),
        "conversion_rate_7d": traffic_7d.get("conversion_rate", 0),
    }


@router.get("/publish-readiness")
async def get_publish_readiness(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """内容分发中心 — 建站 / IP 槽位 / 绑号就绪态。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.publish_readiness_service import build_publish_readiness
    data = await build_publish_readiness(db, tenant=tenant)
    return success_response(data=data)


@router.get("/ai-connect")
def get_client_ai_connect(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """租户 AI 通道 + 英伟达探测摘要；无记录时自动挂免费通道。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.ai_traffic_connect_service import (
        NVIDIA_USAGE_POLICY_NOTICE,
        build_connect_status,
        ensure_tenant_ai_connectivity,
    )
    ensure_tenant_ai_connectivity(db, str(tenant.id))
    db.refresh(tenant)
    status = build_connect_status(db, tenant)
    return success_response(
        data={
            **status,
            "usage_policy_notice": status.get("usage_policy_notice") or NVIDIA_USAGE_POLICY_NOTICE,
        }
    )


@router.get("/ai-traffic-recharge-catalog")
def get_ai_traffic_recharge_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """租户 AI 流量充值目录（大模型平台 + 流量包 + 自定义充值规则）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.ai_traffic_connect_service import (
        FREE_NVIDIA_ALERT_TITLE,
        FREE_NVIDIA_NOTICE,
        NVIDIA_USAGE_POLICY_NOTICE,
        RECHARGE_CTA_SHORT,
        build_connect_status,
        list_providers_with_connect_hints,
        nvidia_free_available,
    )
    from app.services.ai_traffic_provider_service import get_tenant_ai_traffic_provider
    from app.services.order_addon_service import (
        TOKEN_PACK_CATALOG,
        custom_recharge_config_for_client,
    )
    packs = [
        {
            "pack_id": pid,
            "tokens": spec["tokens"],
            "price_cents": spec["price_cents"],
            "label": spec["label"],
            "price_yuan": round(spec["price_cents"] / 100, 2),
        }
        for pid, spec in TOKEN_PACK_CATALOG.items()
    ]
    return success_response(
        data={
            "providers": list_providers_with_connect_hints(db),
            "packs": packs,
            "current_provider_id": get_tenant_ai_traffic_provider(tenant),
            "custom_recharge": custom_recharge_config_for_client(),
            "ai_connect": build_connect_status(db, tenant),
            "free_nvidia_notice": FREE_NVIDIA_NOTICE,
            "free_nvidia_alert_title": FREE_NVIDIA_ALERT_TITLE,
            "recharge_cta": RECHARGE_CTA_SHORT,
            "usage_policy_notice": NVIDIA_USAGE_POLICY_NOTICE,
            "nvidia_free_available": nvidia_free_available(db),
        }
    )


@router.get("/branding")
def get_client_branding(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取客户品牌配置"""
    tenant, link, err = _resolve_tenant(db, current_user)
    if err:
        return err

    brand = TenantBrandConfig()
    if tenant.settings:
        try:
            settings_dict = json.loads(tenant.settings)
            brand_data = settings_dict.get("brand", {})
            if brand_data:
                brand = TenantBrandConfig(**brand_data)
        except (json.JSONDecodeError, TypeError):
            pass

    return success_response(data={
        "company_name": brand.company_name or tenant.name,
        "logo_url": brand.logo_url or "",
        "brand_colors": brand.brand_colors.model_dump(),
        "site_title": brand.site_title or "",
        "slogan": brand.slogan or "",
        "about_summary": brand.about_summary or "",
        "contact_phone": brand.contact_phone or "",
        "contact_email": brand.contact_email or "",
        "footer_text": brand.footer_text or "",
        "custom_css": brand.custom_css or "",
        "tenant_domain": tenant.domain,
        "tenant_status": tenant.status,
    })


@router.get("/wecom-push-config")
def get_wecom_push_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """本租户企微推送配置（销售 UserID 由客户自行填写）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.tenant_wecom_config_service import get_or_create_row, serialize_for_api
    row = get_or_create_row(db, str(tenant.id))
    db.commit()
    return success_response(data=serialize_for_api(row))


@router.put("/wecom-push-config")
def update_wecom_push_config(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """保存本租户企微推送配置。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.tenant_wecom_config_service import upsert_config
    data = upsert_config(
        db,
        str(tenant.id),
        enabled=body.get("enabled"),
        corp_id=body.get("corp_id"),
        agent_id=body.get("agent_id"),
        agent_secret=body.get("agent_secret"),
        push_userids=body.get("push_userids") or body.get("push_userids_text"),
        webhook_url=body.get("webhook_url"),
    )
    return success_response(data=data, message="企微推送配置已保存")


@router.get("/onboarding-guides")
def get_onboarding_guides(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """开户与客户配置手册链接（ITER-03d · 产品内可跳转）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.onboarding_progress_service import (
        build_jtbd_site_checklist,
        build_onboarding_roadmap,
        refresh_onboarding_checklist,
    )
    settings_raw = tenant.settings or "{}"
    try:
        settings_dict = json.loads(settings_raw) if isinstance(settings_raw, str) else settings_raw
    except json.JSONDecodeError:
        settings_dict = {}
    onboarding = settings_dict.get("onboarding") if isinstance(settings_dict.get("onboarding"), dict) else {}
    checklist = refresh_onboarding_checklist(
        db,
        tenant,
        onboarding.get("checklist") if isinstance(onboarding.get("checklist"), list) else None,
    )
    from app.services.journey_health_service import build_journey_health
    journey_health = build_journey_health(db, tenant)
    return success_response(
        data={
            "guides": [
                {
                    "id": "wecom_5min",
                    "title": "企微销售推送 5 分钟配置",
                    "summary": "有人问价，销售手机能收到",
                    "route": "/inquiries/im-routing#wecom-push",
                    "doc": "docs/guides/customer-wecom-push-5min.md",
                },
                {
                    "id": "agent_roadmap",
                    "title": "开户后完整路线（代理可转发）",
                    "summary": "五段大白话：开店→让人看见→客户找得到→销售收得到→天天接单",
                    "route": "/client/onboarding",
                    "doc": "docs/guides/agent-onboarding-roadmap-onepage.md",
                },
                {
                    "id": "auto_negotiator",
                    "title": "抖音评论自动谈单",
                    "summary": "绑抖音后，评论问价自动进列表",
                    "route": "/sales/auto-negotiator",
                },
            ],
            "roadmap": build_onboarding_roadmap(db, tenant, checklist),
            "jtbd_checklist": build_jtbd_site_checklist(tenant),
            "jtbd_contract": "SITE-JTBD-01",
            "journey_health": journey_health,
            "role_insights": journey_health.get("role_insights") or [],
            "qa_checklist": "docs/qa-step5-inquiry-im-acceptance.md",
        }
    )


@router.get("/journey-health")
def get_journey_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """开户主链健康度 + 八角色缺口建议（PM-MKT-02）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.journey_health_service import build_journey_health
    return success_response(data=build_journey_health(db, tenant))


@router.get("/inquiry-weekly")
def get_inquiry_weekly(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """本周询盘 honest 周报：来了几条、跟进了几条（P0-5）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.inquiry_weekly_service import build_inquiry_weekly_report
    return success_response(data=build_inquiry_weekly_report(db, tenant))


@router.get("/today-three")
def get_today_three(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """今日三步：填产品 → 发内容 → 看询盘（P0-2）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.client_today_three_service import build_today_three_payload
    return success_response(data=build_today_three_payload(db, tenant))


@router.post("/douyin-comments/pull")
async def pull_douyin_comments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """租户触发：从 AiToEarn / Inbox 拉取抖音评论并入库（ITER-03b）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    if current_user.role not in ("admin", "super_admin", "tenant_admin", "user"):
        return error_response(403, "权限不足")
    from app.services.douyin_comment_pull_service import pull_and_ingest_for_tenant
    result = await pull_and_ingest_for_tenant(db, str(tenant.id), source="auto")
    msg = "评论拉取完成"
    if result.get("ingested", 0) == 0:
        msg = result.get("hint") or "暂无新评论"
    return success_response(data=result, message=msg)


@router.post("/douyin-comments/rehearsal-ingest")
async def rehearsal_ingest_douyin_comments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """5c 彩排：开发环境投递 1 条测试评论；生产走真实拉取。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.sales_channel_rehearsal_service import run_comment_rehearsal
    result = await run_comment_rehearsal(db, tenant_id=str(tenant.id))
    n = result.get("ingested", 0)
    return success_response(
        data=result,
        message=f"已入库 {n} 条评论" if n else (result.get("hint") or "未入库"),
    )


@router.post("/sales-channel-rehearsal/inbound")
def rehearsal_inbound_inquiry(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """5a 彩排：模拟入站询盘 + 触发企微推送链。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.sales_channel_rehearsal_service import run_inbound_rehearsal
    data = run_inbound_rehearsal(db, tenant_id=str(tenant.id))
    return success_response(data=data, message="入站彩排完成，请到询盘列表查看")


@router.post("/sales-channel-rehearsal/wecom-push")
def rehearsal_wecom_push(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """5b 彩排：发送测试企微通知。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.sales_channel_rehearsal_service import run_wecom_push_rehearsal
    data = run_wecom_push_rehearsal(db, tenant_id=str(tenant.id))
    if data.get("skipped"):
        return success_response(
            data={**data, "ok": False},
            message=data.get("hint") or "企微未配置，请先保存 Corp/Agent/Secret 或配置开发 .env",
        )
    ok = data.get("status") == "sent"
    return success_response(
        data={**data, "ok": ok},
        message="测试推送已发送" if ok else (data.get("error_message") or "推送失败"),
    )
