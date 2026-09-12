"""ECommerceCrawlers 合规门禁 — 无 Sidecar / 无授权 / 无 evidence 一律拒绝。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal

from app.services.crawlers.ecommerce_crawlers_registry import (
    ComplianceTier,
    SpiderRecipe,
)

ComplianceVerdict = Literal["allow", "deny"]


@dataclass(frozen=True)
class ComplianceDecision:
    verdict: ComplianceVerdict
    error_code: str | None = None
    message: str | None = None
    human_review_required: bool = False
    audit_tags: tuple[str, ...] = ()


def _env_true(name: str) -> bool:
    """实现 envtrue 的功能。
    
    :param name: 参数 name（类型: str）
    :return: 返回 bool 结果
    """
    return (os.getenv(name) or "").strip().lower() in ("1", "true", "yes", "on")


def _spider_platform_enabled(spider_id: str) -> bool:
    """实现 spider平台enabled 的功能。
    
    :param spider_id: 参数 spider_id（类型: str）
    :return: 返回 bool 结果
    """
    specific = f"ECOMMERCE_SPIDER_ENABLE_{spider_id.upper()}"
    if _env_true(specific):
        return True
    if _env_true("ECOMMERCE_SPIDERS_ENABLE_ALL"):
        return True
    return False


def _social_spiders_platform_enabled() -> bool:
    """实现 socialspiders平台enabled 的功能。
    
    :return: 返回 bool 结果
    """
    return _env_true("ECOMMERCE_SOCIAL_SPIDERS_ENABLED")


def assert_spider_compliance(
    recipe: SpiderRecipe,
    *,
    params: dict[str, Any] | None,
    tenant_id: str | None,
    operator_role: str | None,
    compliance_acknowledged: bool = False,
    tenant_consent: bool = False,
    purpose: str | None = None,
) -> ComplianceDecision:
    """执行前合规校验；通过方可调用 Sidecar。"""
    params = params or {}
    role = (operator_role or "").lower()
    is_platform_ops = role in ("super_admin", "admin")
    purpose_text = (purpose or params.get("purpose") or "").strip()

    if recipe.compliance == "platform_blocked":
        return ComplianceDecision(
            verdict="deny",
            error_code="SPIDER_PLATFORM_BLOCKED",
            message=recipe.compliance_note or "该 spider 属于黑帽/垃圾 SEO，平台永久禁用",
        )

    if recipe.compliance == "allowed_sidecar":
        if not purpose_text and recipe.requires_purpose:
            return ComplianceDecision(
                verdict="deny",
                error_code="SPIDER_PURPOSE_REQUIRED",
                message="请填写 purpose 说明采集用途",
            )
        return ComplianceDecision(
            verdict="allow",
            human_review_required=False,
            audit_tags=("allowed_sidecar", recipe.id),
        )

    if recipe.compliance == "human_review":
        if not purpose_text:
            return ComplianceDecision(
                verdict="deny",
                error_code="SPIDER_PURPOSE_REQUIRED",
                message="human_review 类 spider 须填写 purpose",
            )
        return ComplianceDecision(
            verdict="allow",
            human_review_required=True,
            audit_tags=("human_review", recipe.id),
        )

    if recipe.compliance == "restricted":
        return _decide_restricted_spider(
            recipe, is_platform_ops, role, params, tenant_consent, compliance_acknowledged, purpose_text, tenant_id
        )

    if recipe.compliance == "social_restricted":
        return _decide_social_restricted_spider(
            recipe, params, tenant_consent, compliance_acknowledged, purpose_text
        )

    return ComplianceDecision(
        verdict="deny",
        error_code="SPIDER_COMPLIANCE_UNKNOWN",
        message=f"未知合规级别 {recipe.compliance}",
    )


def _decide_restricted_spider(recipe, is_platform_ops, role, params, tenant_consent, compliance_acknowledged, purpose_text, tenant_id):
    """对 restricted 级 spider 做逐项合规裁决。"""
    if not _spider_platform_enabled(recipe.id):
        return ComplianceDecision(
            verdict="deny",
            error_code="SPIDER_PLATFORM_NOT_ENABLED",
            message=f"须在 .env 启用 ECOMMERCE_SPIDER_ENABLE_{recipe.id.upper()}=1",
        )
    if not tenant_consent and not params.get("tenant_consent"):
        return ComplianceDecision(
            verdict="deny",
            error_code="SPIDER_TENANT_CONSENT_REQUIRED",
            message="restricted spider 须 tenant_consent=true（租户书面授权）",
        )
    if not compliance_acknowledged and not params.get("compliance_acknowledged"):
        return ComplianceDecision(
            verdict="deny",
            error_code="SPIDER_COMPLIANCE_ACK_REQUIRED",
            message="须 compliance_acknowledged=true，确认遵守 robots/ToS/个保法",
        )
    if not purpose_text:
        return ComplianceDecision(
            verdict="deny",
            error_code="SPIDER_PURPOSE_REQUIRED",
            message="restricted spider 须填写 purpose",
        )
    if not is_platform_ops and role not in ("tenant_admin", "operator"):
        return ComplianceDecision(
            verdict="deny",
            error_code="SPIDER_ROLE_DENIED",
            message="restricted spider 须 tenant_admin/operator 或平台超管触发",
        )
    return ComplianceDecision(
        verdict="allow",
        human_review_required=True,
        audit_tags=("restricted", recipe.id, f"tenant:{tenant_id or 'none'}"),
    )


def _decide_social_restricted_spider(recipe, params, tenant_consent, compliance_acknowledged, purpose_text):
    """对 social_restricted 级 spider 做逐项合规裁决。"""
    if not _social_spiders_platform_enabled():
        return ComplianceDecision(
            verdict="deny",
            error_code="SOCIAL_SPIDERS_NOT_ENABLED",
            message="须 ECOMMERCE_SOCIAL_SPIDERS_ENABLED=1 且 Sidecar 独立部署",
        )
    if not _spider_platform_enabled(recipe.id):
        return ComplianceDecision(
            verdict="deny",
            error_code="SPIDER_PLATFORM_NOT_ENABLED",
            message=f"须 ECOMMERCE_SPIDER_ENABLE_{recipe.id.upper()}=1",
        )
    if not tenant_consent:
        return ComplianceDecision(
            verdict="deny",
            error_code="SPIDER_TENANT_CONSENT_REQUIRED",
            message="社媒 spider 须租户书面授权 tenant_consent=true",
        )
    if not compliance_acknowledged:
        return ComplianceDecision(
            verdict="deny",
            error_code="SPIDER_COMPLIANCE_ACK_REQUIRED",
            message="须确认不采集私信/不自动群发/不共用账号池",
        )
    if not purpose_text or len(purpose_text) < 8:
        return ComplianceDecision(
            verdict="deny",
            error_code="SPIDER_PURPOSE_REQUIRED",
            message="社媒 spider 须填写 ≥8 字 purpose（公开信息研究用途）",
        )
    if params.get("bulk_outreach") or params.get("auto_send"):
        return ComplianceDecision(
            verdict="deny",
            error_code="SPIDER_BULK_OUTREACH_FORBIDDEN",
            message="禁止通过 spider 参数触发 bulk_outreach/auto_send",
        )
    return ComplianceDecision(
        verdict="allow",
        human_review_required=True,
        audit_tags=("social_restricted", recipe.id, "no_account_pool"),
    )


def validate_spider_result(
    recipe: SpiderRecipe,
    data: dict[str, Any],
    *,
    decision: ComplianceDecision,
) -> dict[str, Any]:
    """Sidecar 返回后校验：须有 evidence 或 items；禁止假成功。"""
    items = data.get("items") or data.get("results") or []
    evidence = (data.get("evidence_url") or data.get("source_url") or "").strip()
    if not items and not evidence:
        return {
            "ok": False,
            "error_code": "SPIDER_NO_EVIDENCE",
            "spider_id": recipe.id,
            "note": "Sidecar 未返回 items 或 evidence_url，不得落库为真值",
        }
    max_items = recipe.max_items_per_run
    if isinstance(items, list) and len(items) > max_items:
        items = items[:max_items]
    return {
        "ok": True,
        "spider_id": recipe.id,
        "lane": recipe.lane,
        "compliance": recipe.compliance,
        "human_review_required": decision.human_review_required,
        "probe_mode": "ecommerce_spider",
        "items": items if isinstance(items, list) else [],
        "evidence_url": evidence or None,
        "audit_tags": list(decision.audit_tags),
        "compliance_note": recipe.compliance_note,
        "meta": {k: v for k, v in data.items() if k not in ("items", "results")},
    }
