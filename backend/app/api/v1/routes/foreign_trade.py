# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""外贸 B2B 工具·技能·生态 API — 随源码部署。"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.content_master import ContentMaster
from app.models.inquiry import Inquiry
from app.models.user import User
from app.services.foreign_trade.aeo_fact_audit_service import run_aeo_fact_audit
from app.services.foreign_trade.content_one_to_many_service import expand_one_to_many
from app.services.foreign_trade.inquiry_meddpicc_service import save_meddpicc, score_inquiry_meddpicc
from app.services.foreign_trade.platform_health_alert_service import run_platform_health_alert_cycle
from app.services.foreign_trade.publish_preflight_checklist_service import (
    apply_preflight_checklist,
    validate_preflight,
)
from app.services.foreign_trade.foreign_trade_agent_service import (
    run_inquiry_osint_agent,
    run_inquiry_proforma_agent,
    run_osint_agent,
    run_proforma_agent,
    run_prospect_clean_agent,
    run_website_icp_agent,
)
from app.services.foreign_trade.trade_document_service import build_proforma_invoice
from app.services.foreign_trade.utm_attribution_service import attribution_report
from app.services.foreign_trade.website_icp_service import analyze_website_icp
from app.services.foreign_trade.benchmark_catalog_service import build_benchmark_matrix, list_benchmark_sources
from app.services.foreign_trade_ecosystem_service import (
    build_deploy_manifest,
    build_ecosystem_overview,
    list_b2b_experts,
    list_gaps,
    list_skills,
    load_ecosystem_catalog,
    recommend_integrations_for_gaps,
)
from app.services.foreign_trade.trade_document_export_service import (
    build_proforma_docx,
    build_proforma_pdf,
    build_proforma_print_html,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/foreign-trade", tags=["外贸生态"])


def _staff(user: User) -> bool:
    """
    处理 _staff 相关业务逻辑。

    :param user: 入参 (User)。

    :return: 返回 bool 类型的结果。
    """
    return user.role in ("super_admin", "admin", "tenant_admin", "operator")


@router.get("/ecosystem/overview")
def foreign_trade_ecosystem_overview(current_user: User = Depends(get_current_user)):
    """概览：技能/插件/短板统计（租户 Admin 可读）。"""
    if not _staff(current_user):
        return success_response(data={"note": "login_required_for_detail"}, message="请登录查看详情")
    return success_response(data=build_ecosystem_overview())


@router.get("/ecosystem/catalog")
def foreign_trade_ecosystem_catalog(
    current_user: User = Depends(get_current_user),
    section: str | None = Query(None, description="skills|bundled|sidecars|github|gaps|all"),
):
    """完整或分片目录 JSON。"""
    if not _staff(current_user):
        return success_response(data={}, message="权限不足")
    cat = load_ecosystem_catalog()
    if section == "skills":
        data = {"skills_registry": cat.get("skills_registry")}
    elif section == "bundled":
        data = {"bundled_capabilities": cat.get("bundled_capabilities")}
    elif section == "sidecars":
        data = {"optional_sidecars": cat.get("optional_sidecars")}
    elif section == "github":
        data = {"github_curated": cat.get("github_curated")}
    elif section == "gaps":
        data = {"open_gaps_p0": cat.get("open_gaps_p0"), "gap_summary": cat.get("gap_summary")}
    elif section == "benchmarks":
        data = {
            "benchmark_sources": cat.get("benchmark_sources"),
            "capability_benchmark_matrix": cat.get("capability_benchmark_matrix"),
            "external_nav": cat.get("external_nav"),
        }
    else:
        data = cat
    return success_response(data=data)


@router.get("/integrations/sidecars/status")
def foreign_trade_sidecars_status(current_user: User = Depends(get_current_user)):
    """找客 / Headless / DeerFlow 旁路就绪态（只读）。"""
    if not _staff(current_user):
        return success_response(data={}, message="权限不足")
    from app.services.foreign_trade.integrations_sidecars_status_service import (
        build_integrations_sidecars_status,
    )
    return success_response(data=build_integrations_sidecars_status())


@router.get("/integrations/matrix-oauth-gate")
def matrix_oauth_gate(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    platforms: str | None = Query(None, description="逗号分隔平台名，空则默认矩阵"),
):
    """GW-S-MAT-01 矩阵 OAuth + Worker 双门禁报告。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    from app.api.v1.routes.client import _resolve_tenant as client_resolve
    from app.services.foreign_trade.matrix_oauth_publish_gate_service import matrix_oauth_gate_report
    tenant, _, err = client_resolve(db, current_user)
    if err and current_user.role in ("super_admin", "admin"):
        from app.models.tenant import Tenant
        tenant = db.query(Tenant).filter(Tenant.domain == "dev.local").first()
        err = None if tenant else err
    if err:
        return err
    names = [p.strip() for p in (platforms or "").split(",") if p.strip()] or None
    return success_response(
        data=matrix_oauth_gate_report(db, tenant_id=str(tenant.id), platform_names=names)
    )


class LinkedInDecisionMakerBody(BaseModel):
    company: str = Field(..., min_length=2, max_length=200)
    domain: str = Field("", max_length=253)
    industry: str = Field("", max_length=120)
    purpose: str = Field(..., min_length=8, max_length=500)
    tenant_consent: bool = False
    compliance_acknowledged: bool = False
    max_results: int = Field(5, ge=1, le=10)


@router.post("/integrations/linkedin/decision-makers")
def linkedin_decision_makers(
    body: LinkedInDecisionMakerBody,
    current_user: User = Depends(get_current_user),
):
    """P3 LinkedIn 决策人 enrichment — restricted，须 consent + evidence。"""
    if current_user.role not in ("super_admin", "admin", "tenant_admin", "operator"):
        return error_response(403, "权限不足")
    if not body.tenant_consent:
        return error_response(403, "SPIDER_TENANT_CONSENT_REQUIRED")
    if not body.compliance_acknowledged:
        return error_response(403, "SPIDER_COMPLIANCE_ACK_REQUIRED")
    from app.services.ubrain.linkedin_decision_maker_sidecar import fetch_decision_makers
    tenant_id = getattr(current_user, "tenant_id", None)
    pack = fetch_decision_makers(
        company=body.company,
        domain=body.domain,
        industry=body.industry,
        tenant_id=str(tenant_id) if tenant_id else None,
        max_results=body.max_results,
    )
    if not pack:
        return error_response(
            503,
            "LinkedIn Sidecar 未配置或无 evidence 联系人；请部署 LINKEDIN_DECISION_MAKER_URL",
        )
    return success_response(
        data={
            **pack,
            "purpose": body.purpose,
            "disclaimer": "LinkedIn 结果须人工核实；禁止未授权自动触达",
        }
    )


@router.get("/trade-intel/customs-buyer-brief")
def customs_buyer_brief(
    product: str = Query(..., min_length=2, max_length=200),
    hs_code: str | None = Query(None, max_length=32),
    country_code: str | None = Query(None, max_length=8),
    include_sidecar: bool = Query(False, description="合并 CustomsDataSpider Sidecar 买家线索"),
    current_user: User = Depends(get_current_user),
):
    """海关公开统计 + 买家反查 playbook（Sidecar 买家须 evidence_url）。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    from app.services.foreign_trade.customs_buyer_brief_service import build_customs_buyer_brief
    tenant_id = getattr(current_user, "tenant_id", None)
    return success_response(
        data=build_customs_buyer_brief(
            product=product,
            hs_code=hs_code,
            country_code=country_code,
            include_sidecar=include_sidecar,
            tenant_id=str(tenant_id) if tenant_id else None,
        )
    )


class CustomsBuyerResearchBody(BaseModel):
    product: str = Field(..., min_length=2, max_length=200)
    hs_code: str | None = Field(None, max_length=32)
    country_code: str | None = Field(None, max_length=8)
    purpose: str = Field(..., min_length=8, max_length=500)
    tenant_consent: bool = False
    compliance_acknowledged: bool = False
    max_results: int = Field(8, ge=1, le=20)


@router.post("/integrations/customs/buyer-research")
def customs_buyer_research(
    body: CustomsBuyerResearchBody,
    current_user: User = Depends(get_current_user),
):
    """P4 CustomsDataSpider 买家反查 — restricted，须 consent + evidence。"""
    if current_user.role not in ("super_admin", "admin", "tenant_admin", "operator"):
        return error_response(403, "权限不足")
    if not body.tenant_consent:
        return error_response(403, "SPIDER_TENANT_CONSENT_REQUIRED")
    if not body.compliance_acknowledged:
        return error_response(403, "SPIDER_COMPLIANCE_ACK_REQUIRED")
    from app.services.foreign_trade.customs_buyer_brief_service import build_customs_buyer_brief
    tenant_id = getattr(current_user, "tenant_id", None)
    brief = build_customs_buyer_brief(
        product=body.product,
        hs_code=body.hs_code,
        country_code=body.country_code,
        include_sidecar=True,
        tenant_id=str(tenant_id) if tenant_id else None,
        limit=body.max_results,
    )
    if not brief.get("buyer_history"):
        return error_response(
            503,
            "CustomsDataSpider Sidecar 未配置或无带 evidence 的买家线索；请部署 CUSTOMS_DATA_SPIDER_URL",
        )
    return success_response(
        data={
            **brief,
            "purpose": body.purpose,
            "disclaimer": "海关买家线索须人工核实；禁止无授权触达或冒充已收录",
        }
    )


class EcommerceSpiderRunBody(BaseModel):
    spider_id: str = Field(..., min_length=1, max_length=64)
    params: dict[str, Any] = Field(default_factory=dict)
    purpose: str | None = Field(None, max_length=500, description="采集用途说明")
    compliance_acknowledged: bool = Field(
        False, description="restricted/social 须 true：确认 robots/ToS/不自动群发"
    )
    tenant_consent: bool = Field(False, description="restricted/social 须租户书面授权")


@router.get("/integrations/ecommerce-crawlers/registry")
def ecommerce_crawlers_registry(current_user: User = Depends(get_current_user)):
    """ECommerceCrawlers 子项目 → 本系统 Lane 映射（只读）。"""
    if not _staff(current_user):
        return success_response(data={}, message="权限不足")
    from app.services.crawlers.ecommerce_crawlers_registry import registry_payload
    return success_response(data=registry_payload())


class EcommerceQuickRunBody(BaseModel):
    preset: str = Field(..., min_length=1, max_length=64, description="baidu|qichacha|或 spider_id")
    keyword: str | None = Field(None, max_length=200)
    site: str | None = Field(None, max_length=500)
    purpose: str | None = Field(None, max_length=500)
    tenant_consent: bool = False
    compliance_acknowledged: bool = False


@router.get("/integrations/ecommerce-crawlers/panel")
def ecommerce_crawlers_panel(current_user: User = Depends(get_current_user)):
    """数据采集旁路 — 大白话状态（管理端一页看懂）。"""
    if not _staff(current_user):
        return success_response(data={}, message="权限不足")
    from app.services.crawlers.ecommerce_crawlers_smart import build_panel
    return success_response(data=build_panel())


@router.post("/integrations/ecommerce-crawlers/quick-run")
def ecommerce_crawlers_quick_run(
    body: EcommerceQuickRunBody,
    current_user: User = Depends(get_current_user),
):
    """一键探测：只需 preset + 关键词。"""
    if current_user.role not in ("super_admin", "admin", "tenant_admin", "operator"):
        return error_response(403, "权限不足")
    from app.services.crawlers.ecommerce_crawlers_smart import quick_run
    tenant_id = getattr(current_user, "tenant_id", None)
    result = quick_run(
        body.preset,
        keyword=body.keyword,
        site=body.site,
        tenant_id=str(tenant_id) if tenant_id else None,
        operator_role=current_user.role,
        tenant_consent=body.tenant_consent,
        compliance_acknowledged=body.compliance_acknowledged,
        purpose=body.purpose,
    )
    if not result.get("ok"):
        err = result.get("error_code") or "SPIDER_RUN_FAILED"
        code = 503 if err.endswith("NOT_CONFIGURED") else 400
        if err in ("SPIDER_PLATFORM_BLOCKED", "SOCIAL_SPIDERS_NOT_ENABLED", "SPIDER_ROLE_DENIED"):
            code = 403
        return error_response(code, result.get("message_zh") or err)
    return success_response(data=result)


@router.post("/integrations/ecommerce-crawlers/run")
def ecommerce_crawlers_run(
    body: EcommerceSpiderRunBody,
    current_user: User = Depends(get_current_user),
):
    """触发 Sidecar spider（合规门禁 + evidence 校验）。"""
    from app.services.crawlers.ecommerce_crawlers_registry import recipe_by_id
    from app.services.crawlers.ecommerce_crawlers_sidecar import run_spider
    recipe = recipe_by_id(body.spider_id.strip().lower())
    if not recipe:
        return error_response(400, "SPIDER_UNKNOWN")
    role = current_user.role
    if recipe.compliance in ("restricted", "social_restricted"):
        if role not in ("super_admin", "admin", "tenant_admin", "operator"):
            return error_response(403, "该 spider 须 tenant_admin 或平台运维")
    elif role not in ("super_admin", "admin", "tenant_admin", "operator"):
        return error_response(403, "权限不足")

    tenant_id = getattr(current_user, "tenant_id", None)
    purpose = body.purpose
    consent = body.tenant_consent
    ack = body.compliance_acknowledged
    from app.services.crawlers.ecommerce_crawlers_smart import apply_run_defaults, enrich_result_zh
    purpose, consent, ack = apply_run_defaults(
        spider_id=body.spider_id.strip().lower(),
        operator_role=role,
        purpose=purpose,
        tenant_consent=consent,
        compliance_acknowledged=ack,
    )
    result = run_spider(
        body.spider_id.strip().lower(),
        params=body.params,
        tenant_id=str(tenant_id) if tenant_id else None,
        operator_role=role,
        compliance_acknowledged=ack,
        tenant_consent=consent,
        purpose=purpose,
    )
    result = enrich_result_zh(result)
    if not result.get("ok"):
        err = result.get("error_code") or "SPIDER_RUN_FAILED"
        code = 503 if err.endswith("NOT_CONFIGURED") else 400
        if err in (
            "SPIDER_PLATFORM_BLOCKED",
            "SPIDER_BULK_OUTREACH_FORBIDDEN",
            "SOCIAL_SPIDERS_NOT_ENABLED",
            "SPIDER_ROLE_DENIED",
        ):
            code = 403
        return error_response(code, result.get("message_zh") or err)
    return success_response(data=result)


class UserActionQuickRunBody(BaseModel):
    preset: str = Field(..., min_length=1, max_length=64, description="conversion|session|hot_products|...")
    params: dict[str, Any] = Field(default_factory=dict)
    purpose: str | None = Field(None, max_length=500)
    tenant_consent: bool = False
    compliance_acknowledged: bool = False


@router.get("/integrations/user-action-analytics/registry")
def user_action_analytics_registry(current_user: User = Depends(get_current_user)):
    """
    处理 user_action_analytics_registry 相关业务逻辑。

    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if not _staff(current_user):
        return success_response(data={}, message="权限不足")
    from app.services.analytics.user_action_analytics_registry import registry_payload
    return success_response(data=registry_payload())


@router.post("/integrations/user-action-analytics/quick-run")
def user_action_analytics_quick_run(
    body: UserActionQuickRunBody,
    current_user: User = Depends(get_current_user),
):
    """一键 Spark 行为分析（页面转化 / 热门商品等）。"""
    if current_user.role not in ("super_admin", "admin", "tenant_admin", "operator"):
        return error_response(403, "权限不足")
    from app.services.analytics.user_action_analytics_smart import quick_run
    tenant_id = getattr(current_user, "tenant_id", None)
    result = quick_run(
        body.preset,
        params=body.params,
        tenant_id=str(tenant_id) if tenant_id else None,
        operator_role=current_user.role,
        tenant_consent=body.tenant_consent,
        compliance_acknowledged=body.compliance_acknowledged,
        purpose=body.purpose,
    )
    if not result.get("ok"):
        err = result.get("error_code") or "ANALYTICS_RUN_FAILED"
        code = 503 if err.endswith("NOT_CONFIGURED") else 400
        if err in ("ANALYTICS_MODULE_BLOCKED", "ANALYTICS_ROLE_DENIED"):
            code = 403
        return error_response(code, result.get("message_zh") or err)
    return success_response(data=result)


@router.get("/ecosystem/skills")
def foreign_trade_skills(
    current_user: User = Depends(get_current_user),
    status: str | None = Query(None, description="covered|partial|gap|reference"),
    category: str | None = None,
):
    """
    处理 foreign_trade_skills 相关业务逻辑。

    :param current_user: 入参 (User)。
    :param status: 入参 (str | None)。
    :param category: 入参 (str | None)。

    :return: 返回处理结果（或 None）。
    """
    if not _staff(current_user):
        return success_response(data={"items": []}, message="权限不足")
    items = list_skills(status=status, category=category)
    return success_response(data={"items": items, "total": len(items)})


@router.get("/ecosystem/github-scout")
def foreign_trade_github_scout(
    current_user: User = Depends(get_current_user),
    force: bool = Query(False, description="忽略小时去重，立即侦察"),
):
    """GitHub 生态侦察 — 专家代搜，用户只需看 Inbox 点同意。"""
    if not _staff(current_user):
        return success_response(data={}, message="权限不足")
    from app.services.hermes.github_ecosystem_scout_service import (
        load_scout_snapshot,
        run_github_scout_cycle,
    )
    if force:
        data = run_github_scout_cycle(force=True)
    else:
        data = load_scout_snapshot() or run_github_scout_cycle(force=False)
    return success_response(
        data=data,
        message=(data or {}).get("user_message_zh") or "GitHub 侦察完成",
    )


@router.get("/ecosystem/gaps")
def foreign_trade_gaps(
    current_user: User = Depends(get_current_user),
    priority: str = Query("P0"),
):
    """
    处理 foreign_trade_gaps 相关业务逻辑。

    :param current_user: 入参 (User)。
    :param priority: 入参 (str)。

    :return: 返回处理结果（或 None）。
    """
    if not _staff(current_user):
        return success_response(data={"items": []}, message="权限不足")
    gaps = list_gaps(priority=priority)
    rec = recommend_integrations_for_gaps()
    return success_response(
        data={
            "gaps": gaps,
            "recommended_integrations": rec,
        }
    )


@router.get("/ecosystem/deploy-manifest")
def foreign_trade_deploy_manifest(current_user: User = Depends(get_current_user)):
    """运维：随源码部署清单 + optional compose 路径。"""
    if current_user.role not in ("super_admin", "admin"):
        return success_response(data={}, message="仅平台运维可查看 deploy-manifest")
    return success_response(data=build_deploy_manifest())


class MeddpiccUpdate(BaseModel):
    metrics: Optional[str] = None
    economic_buyer: Optional[str] = None
    decision_criteria: Optional[str] = None
    decision_process: Optional[str] = None
    paper_process: Optional[str] = None
    identify_pain: Optional[str] = None
    champion: Optional[str] = None
    competition: Optional[str] = None


class ExpandVariantsRequest(BaseModel):
    platforms: list[str] = Field(..., min_length=1)
    include_outreach: bool = True


class PreflightRequest(BaseModel):
    content_master_id: Optional[str] = None
    checklist: dict[str, bool] = Field(default_factory=dict)
    force: bool = False
    persist: bool = True


class OsintCheckRequest(BaseModel):
    target: str = Field(..., min_length=3, description="邮箱 / 域名 / 公司名")
    include_sanctions: bool = True
    include_tech_stack: bool = True
    include_linkedin: bool = True


class WebsiteIcpRequest(BaseModel):
    website_url: str = Field(..., min_length=4)
    max_pages: int = Field(5, ge=1, le=10)
    tenant_id: Optional[str] = Field(None, description="写入 ICP 记忆时必填")


class ProformaInvoiceRequest(BaseModel):
    seller: dict[str, Any]
    buyer: dict[str, Any]
    lines: list[dict[str, Any]] = Field(..., min_length=1)
    currency: str = "USD"
    payment_terms: str = "30% deposit, 70% before shipment"
    delivery_terms: str = "FOB"
    validity_days: int = 15
    notes: str = ""


class ProspectCleanRequest(BaseModel):
    customers: list[dict[str, Any]] = Field(..., min_length=1)
    existing: list[dict[str, Any]] = Field(default_factory=list)


@router.get("/attribution/report")
def foreign_trade_attribution_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tenant_id: Optional[str] = Query(None),
    campaign: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """GW-P-TR-01 UTM 归因报表 + GW-P-GSC-02 GSC/Ads 信号。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    return success_response(
        data=attribution_report(db, tenant_id=tenant_id, campaign=campaign, limit=limit)
    )


@router.get("/attribution/gsc-ads-status")
def foreign_trade_gsc_ads_status(current_user: User = Depends(get_current_user)):
    """GW-P-GSC-02 webhook 就绪态（只读）。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    from app.services.foreign_trade.gsc_ads_attribution_webhook_service import gsc_ads_webhook_status
    return success_response(data=gsc_ads_webhook_status())


@router.post("/attribution/gsc-ads-webhook")
async def foreign_trade_gsc_ads_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_signature: str | None = Header(None, alias="X-Signature"),
    x_timestamp: str | None = Header(None, alias="X-Timestamp"),
):
    """GW-P-GSC-02 接收 GSC/Ads 归因信号（HMAC，无用户 JWT）。"""
    from app.services.foreign_trade.gsc_ads_attribution_webhook_service import (
        ingest_gsc_ads_webhook,
        validate_webhook_request,
    )
    body = await request.body()
    ok, err = validate_webhook_request(
        body=body,
        signature=x_signature,
        timestamp=x_timestamp,
    )
    if not ok:
        code = 503 if err == "GSC_ADS_WEBHOOK_NOT_CONFIGURED" else 403
        return error_response(code, err or "webhook_rejected")

    try:
        import json
        payload = json.loads(body)
        if not isinstance(payload, dict):
            return error_response(400, "INVALID_JSON")
    except json.JSONDecodeError:
        return error_response(400, "INVALID_JSON")

    result = ingest_gsc_ads_webhook(db, payload=payload)
    return success_response(data=result)


@router.get("/inquiries/{inquiry_id}/meddpicc")
def foreign_trade_inquiry_meddpicc(
    inquiry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """GW-L-DC-01 询盘 MEDDPICC 评分。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    row = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not row:
        return error_response(404, "询盘不存在")
    return success_response(data=score_inquiry_meddpicc(row))


@router.put("/inquiries/{inquiry_id}/meddpicc")
def foreign_trade_update_meddpicc(
    inquiry_id: str,
    body: MeddpiccUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    处理 foreign_trade_update_meddpicc 相关业务逻辑。

    :param inquiry_id: 入参 (str)。
    :param body: 入参 (MeddpiccUpdate)。
    :param current_user: 入参 (User)。
    :param db: 入参 (Session)。

    :return: 返回处理结果（或 None）。
    """
    if not _staff(current_user):
        return error_response(403, "权限不足")
    row = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not row:
        return error_response(404, "询盘不存在")
    payload = body.model_dump(exclude_none=True)
    save_meddpicc(db, row, payload)
    return success_response(data=score_inquiry_meddpicc(row))


@router.post("/content-masters/{master_id}/expand-variants")
def foreign_trade_expand_variants(
    master_id: str,
    body: ExpandVariantsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """GW-G-CC-02 1→N 内容变体 + 开发信摘要。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    master = db.query(ContentMaster).filter(ContentMaster.id == master_id).first()
    if not master:
        return error_response(404, "母版不存在")
    data = expand_one_to_many(
        db,
        master=master,
        platforms=body.platforms,
        include_outreach=body.include_outreach,
    )
    return success_response(data=data)


@router.post("/publish/preflight")
def foreign_trade_publish_preflight(
    body: PreflightRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """GW-G-CC-04 发布前人审清单。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    master = None
    if body.content_master_id:
        master = db.query(ContentMaster).filter(ContentMaster.id == body.content_master_id).first()
        if master and body.persist and body.checklist:
            apply_preflight_checklist(
                master,
                body.checklist,
                user_id=str(current_user.id),
            )
            db.commit()
    return success_response(data=validate_preflight(master, body.checklist, force=body.force))


@router.get("/aeo/fact-audit")
def foreign_trade_aeo_fact_audit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tenant_id: Optional[str] = Query(None),
):
    """GW-G-AEO-01 事实一致审计。"""
    if current_user.role not in ("super_admin", "admin"):
        return error_response(403, "仅平台运维可执行 AEO 审计")
    return success_response(data=run_aeo_fact_audit(db, tenant_id=tenant_id))


@router.post("/platform-health/scan")
def foreign_trade_platform_health_scan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    hours: int = Query(24, ge=1, le=168),
    notify: bool = Query(True),
):
    """GW-G-SM-04 账号健康扫描 + 可选飞书告警。"""
    if current_user.role not in ("super_admin", "admin"):
        return error_response(403, "仅平台运维可触发健康扫描")
    return success_response(data=run_platform_health_alert_cycle(db, hours=hours, notify=notify))


@router.post("/osint/check")
def foreign_trade_osint_check(
    body: OsintCheckRequest,
    current_user: User = Depends(get_current_user),
):
    """6 层 OSINT 背调（smart-trade-ai 改编）。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    return success_response(data=run_osint_agent(
        body.target,
        include_sanctions=body.include_sanctions,
        include_tech_stack=body.include_tech_stack,
        include_linkedin=body.include_linkedin,
    ))


@router.post("/website/icp-profile")
def foreign_trade_website_icp(
    body: WebsiteIcpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """官网 ICP 画像（sale_agent_factory 改编）。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    if body.tenant_id:
        return success_response(
            data=run_website_icp_agent(
                db,
                body.tenant_id,
                website_url=body.website_url,
                max_pages=body.max_pages,
                persist_memory=True,
            )
        )
    return success_response(data=analyze_website_icp(body.website_url, max_pages=body.max_pages))


@router.post("/inquiries/{inquiry_id}/osint")
def foreign_trade_inquiry_osint(
    inquiry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """询盘一键背调。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    row = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not row:
        return error_response(404, "询盘不存在")
    return success_response(data=run_inquiry_osint_agent(db, row))


@router.post("/inquiries/{inquiry_id}/proforma-invoice")
def foreign_trade_inquiry_proforma(
    inquiry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """询盘一键生成 PI 草稿。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    row = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not row:
        return error_response(404, "询盘不存在")
    if not row.tenant_id:
        return error_response(400, "询盘未绑定租户")
    return success_response(data=run_inquiry_proforma_agent(db, str(row.tenant_id), row))


@router.post("/documents/proforma-invoice")
def foreign_trade_proforma_invoice(
    body: ProformaInvoiceRequest,
    current_user: User = Depends(get_current_user),
):
    """形式发票 PI / 报价单 Markdown（smart-trade-ai 改编）。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    return success_response(data=build_proforma_invoice(**body.model_dump()))


@router.post("/prospects/clean")
def foreign_trade_prospect_clean(
    body: ProspectCleanRequest,
    current_user: User = Depends(get_current_user),
):
    """潜客去重与打标（Eric_Frank 改编）。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    return success_response(data=run_prospect_clean_agent(body.customers, existing=body.existing))


@router.get("/ecosystem/experts")
def foreign_trade_b2b_experts(current_user: User = Depends(get_current_user)):
    """B2B 外贸 AI 专家团队（b2b_trade_experts.json）。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    return success_response(data=list_b2b_experts())


@router.post("/documents/proforma-invoice/export")
def foreign_trade_proforma_export(
    body: ProformaInvoiceRequest,
    current_user: User = Depends(get_current_user),
    fmt: str = Query("docx", description="docx|html|markdown|pdf"),
):
    """导出 PI：DOCX / HTML / Markdown / PDF。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    doc = build_proforma_invoice(**body.model_dump())
    pi_no = str(doc.get("pi_no") or "PI").replace("/", "-")
    if fmt == "html":
        content = build_proforma_print_html(doc)
        return Response(
            content=content.encode("utf-8"),
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{pi_no}.html"'},
        )
    if fmt == "markdown":
        md = str(doc.get("markdown") or "")
        return Response(
            content=md.encode("utf-8"),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{pi_no}.md"'},
        )
    if fmt == "pdf":
        blob = build_proforma_pdf(doc)
        return Response(
            content=blob,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{pi_no}.pdf"'},
        )
    blob = build_proforma_docx(doc)
    return Response(
        content=blob,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{pi_no}.docx"'},
    )


@router.get("/ecosystem/benchmarks")
def foreign_trade_benchmarks(
    current_user: User = Depends(get_current_user),
    category: str | None = Query(None, description="full_stack_agent|lead_hunter|crm_edm|navigation|..."),
):
    """取长补短：标杆来源 + 能力对照矩阵。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    data = build_benchmark_matrix()
    if category:
        data["sources_filtered"] = list_benchmark_sources(category=category)
    return success_response(data=data)
