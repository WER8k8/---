"""UserActionAnalyzePlatform 合规门禁。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal

from app.services.analytics.user_action_analytics_registry import AnalyticsModule

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


def _module_platform_enabled(module_id: str) -> bool:
    """实现 module平台enabled 的功能。
    
    :param module_id: 参数 module_id（类型: str）
    :return: 返回 bool 结果
    """
    specific = f"USER_ACTION_MODULE_ENABLE_{module_id.upper()}"
    if _env_true(specific):
        return True
    if _env_true("USER_ACTION_MODULES_ENABLE_ALL"):
        return True
    return False


def assert_module_compliance(
    module: AnalyticsModule,
    *,
    params: dict[str, Any] | None,
    tenant_id: str | None,
    operator_role: str | None,
    compliance_acknowledged: bool = False,
    tenant_consent: bool = False,
    purpose: str | None = None,
) -> ComplianceDecision:
    """实现 assertmodulecompliance 的功能。
    
    :param module: 参数 module（类型: AnalyticsModule）
    :param params: 参数 params（类型: dict[str, Any] | None）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param operator_role: 参数 operator_role（类型: str | None）
    :param compliance_acknowledged: 参数 compliance_acknowledged（类型: bool）
    :param tenant_consent: 参数 tenant_consent（类型: bool）
    :param purpose: 参数 purpose（类型: str | None）
    :return: 返回 ComplianceDecision 结果
    """
    params = params or {}
    role = (operator_role or "").lower()
    purpose_text = (purpose or params.get("purpose") or "").strip()
    if module.compliance == "platform_blocked":
        return ComplianceDecision(
            verdict="deny",
            error_code="ANALYTICS_MODULE_BLOCKED",
            message="该分析模块已永久禁用",
        )

    if not purpose_text and module.requires_purpose:
        return ComplianceDecision(
            verdict="deny",
            error_code="ANALYTICS_PURPOSE_REQUIRED",
            message="请填写分析用途（例如：独立站页面转化优化）",
        )

    if module.compliance == "allowed_sidecar":
        return ComplianceDecision(
            verdict="allow",
            human_review_required=False,
            audit_tags=("allowed_sidecar", module.id),
        )

    if module.compliance == "human_review":
        return ComplianceDecision(
            verdict="allow",
            human_review_required=True,
            audit_tags=("human_review", module.id),
        )

    if module.compliance == "restricted":
        if not _module_platform_enabled(module.id):
            return ComplianceDecision(
                verdict="deny",
                error_code="ANALYTICS_MODULE_NOT_ENABLED",
                message=f"须在服务器启用 USER_ACTION_MODULE_ENABLE_{module.id.upper()}=1",
            )
        if not tenant_consent and not params.get("tenant_consent"):
            return ComplianceDecision(
                verdict="deny",
                error_code="ANALYTICS_TENANT_CONSENT_REQUIRED",
                message="Session 类分析须租户授权 tenant_consent=true",
            )
        if not compliance_acknowledged and not params.get("compliance_acknowledged"):
            return ComplianceDecision(
                verdict="deny",
                error_code="ANALYTICS_COMPLIANCE_ACK_REQUIRED",
                message="须确认遵守个保法，不批量导出用户标识",
            )
        if role not in ("super_admin", "admin", "tenant_admin", "operator"):
            return ComplianceDecision(
                verdict="deny",
                error_code="ANALYTICS_ROLE_DENIED",
                message="须租户管理员或平台运维触发",
            )
        return ComplianceDecision(
            verdict="allow",
            human_review_required=True,
            audit_tags=("restricted", module.id, f"tenant:{tenant_id or 'none'}"),
        )

    return ComplianceDecision(
        verdict="deny",
        error_code="ANALYTICS_COMPLIANCE_UNKNOWN",
        message=f"未知合规级别 {module.compliance}",
    )


def validate_analytics_result(
    module: AnalyticsModule,
    data: dict[str, Any],
    *,
    decision: ComplianceDecision,
) -> dict[str, Any]:
    """实现 校验analytics结果 的功能。
    
    :param module: 参数 module（类型: AnalyticsModule）
    :param data: 参数 data（类型: dict[str, Any]）
    :param decision: 参数 decision（类型: ComplianceDecision）
    :return: 返回 dict[str, Any] 结果
    """
    items = data.get("items") or data.get("rows") or data.get("results") or []
    job_id = (data.get("job_id") or data.get("spark_job_id") or "").strip()
    evidence = (data.get("evidence_url") or data.get("report_url") or "").strip()
    probe_mode = data.get("probe_mode") or "user_action_analytics"
    if probe_mode == "stub" and not _env_true("USER_ACTION_ANALYTICS_ALLOW_STUB"):
        return {
            "ok": False,
            "error_code": "ANALYTICS_STUB_NOT_ALLOWED",
            "module_id": module.id,
            "note": "生产环境禁止 stub 分析结果",
        }

    if not items and not job_id and not evidence:
        return {
            "ok": False,
            "error_code": "ANALYTICS_NO_EVIDENCE",
            "module_id": module.id,
            "note": "Sidecar 未返回 items/job_id/evidence，不得展示为实盘",
        }

    if isinstance(items, list) and len(items) > module.max_rows:
        items = items[: module.max_rows]

    return {
        "ok": True,
        "module_id": module.id,
        "lane": module.lane,
        "compliance": module.compliance,
        "human_review_required": decision.human_review_required,
        "probe_mode": probe_mode,
        "items": items if isinstance(items, list) else [],
        "job_id": job_id or None,
        "evidence_url": evidence or None,
        "audit_tags": list(decision.audit_tags),
        "meta": {
            k: v
            for k, v in data.items()
            if k not in ("items", "rows", "results", "probe_mode")
        },
    }
