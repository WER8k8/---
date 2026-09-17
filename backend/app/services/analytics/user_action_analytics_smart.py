# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""UserActionAnalyzePlatform 智能层 — 中文状态与一键分析。"""

from __future__ import annotations

from typing import Any

from app.services.analytics.user_action_analytics_registry import ANALYTICS_MODULES
from app.services.analytics.user_action_analytics_sidecar import (
    run_analytics_module,
    user_action_analytics_sidecar_status,
)

ERROR_HINTS_ZH: dict[str, str] = {
    "ANALYTICS_MODULE_UNKNOWN": "未识别的分析类型",
    "ANALYTICS_MODULE_BLOCKED": "该分析模块已禁用",
    "ANALYTICS_PURPOSE_REQUIRED": "请填写分析用途",
    "ANALYTICS_MODULE_NOT_ENABLED": "平台尚未开通此分析项，请联系运维",
    "ANALYTICS_TENANT_CONSENT_REQUIRED": "Session 分析须租户授权",
    "ANALYTICS_COMPLIANCE_ACK_REQUIRED": "须确认个保与数据使用规范",
    "ANALYTICS_ROLE_DENIED": "当前账号无权触发",
    "USER_ACTION_ANALYTICS_NOT_CONFIGURED": "行为分析服务未部署",
    "USER_ACTION_ANALYTICS_SIDECAR_ERROR": "分析服务无响应",
    "VENDOR_NOT_INSTALLED": "上游项目未克隆，请运行 install-user-action-analytics-vendor.ps1",
    "SPARK_JOB_FAILED": "Spark 作业失败，请检查 vendor 构建与 MySQL",
    "ANALYTICS_NO_EVIDENCE": "未完成真实 Spark 任务，结果不会展示",
    "ANALYTICS_STUB_NOT_ALLOWED": "生产环境禁止 mock 分析数据",
}

QUICK_PRESETS: dict[str, str] = {
    "conversion": "page_conversion",
    "page_conversion": "page_conversion",
    "funnel": "page_conversion",
    "session": "session_analysis",
    "hot_products": "hot_products",
    "ad_traffic": "ad_traffic_realtime",
}


def _sidecar_label(st: dict[str, Any]) -> tuple[str, str]:
    """实现 sidecarlabel 的功能。
    
    :param st: 参数 st（类型: dict[str, Any]）
    :return: 返回 tuple[str, str] 结果
    """
    if not st.get("configured"):
        return "未接入", "Spark 分析集群尚未配置，系统不会伪造转化数据"
    if st.get("healthy"):
        return "已就绪", "可查询页面转化、热门商品等 Spark 报表"
    return "不可达", st.get("detail") or "地址已配置但 Sidecar 未响应"


def build_panel_slice() -> dict[str, Any]:
    """实现 构建panelslice 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    st = user_action_analytics_sidecar_status()
    label, hint = _sidecar_label(st)
    featured = [
        {
            "id": m.id,
            "name": m.name,
            "summary": m.summary,
            "compliance": m.compliance,
        }
        for m in ANALYTICS_MODULES
        if m.id in ("page_conversion", "hot_products", "session_analysis", "ad_traffic_realtime")
    ]
    return {
        "id": "user_action_analytics",
        "name": "电商用户行为分析（Spark）",
        "status": label,
        "hint": hint,
        "github": "oeljeklaus-you/UserActionAnalyzePlatform",
        "featured_modules": featured,
    }


def conversion_summary_for_growth() -> dict[str, Any]:
    """实现 conversionsummaryforgrowth 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    st = user_action_analytics_sidecar_status()
    label, hint = _sidecar_label(st)
    return {
        "title": "页面转化分析",
        "status": label,
        "hint": hint,
        "configured": st.get("configured"),
        "healthy": st.get("healthy"),
        "quick_action": "conversion",
        "note": "基于 Spark 单跳转化率；与 UTM 询盘归因互补，不替代 PostHog/RUM",
    }


def resolve_module_id(preset_or_id: str) -> str | None:
    """实现 解析moduleID 的功能。
    
    :param preset_or_id: 参数 preset_or_id（类型: str）
    :return: 返回 str | None 结果
    """
    key = (preset_or_id or "").strip().lower()
    if any(m.id == key for m in ANALYTICS_MODULES):
        return key
    return QUICK_PRESETS.get(key)


def apply_run_defaults(
    *,
    module_id: str,
    operator_role: str | None,
    purpose: str | None,
    tenant_consent: bool,
    compliance_acknowledged: bool,
) -> tuple[str, bool, bool]:
    """实现 应用执行defaults 的功能。
    
    :param module_id: 参数 module_id（类型: str）
    :param operator_role: 参数 operator_role（类型: str | None）
    :param purpose: 参数 purpose（类型: str | None）
    :param tenant_consent: 参数 tenant_consent（类型: bool）
    :param compliance_acknowledged: 参数 compliance_acknowledged（类型: bool）
    :return: 返回 tuple[str, bool, bool] 结果
    """
    role = (operator_role or "").lower()
    defaults = {
        "page_conversion": "独立站页面单跳转化分析",
        "hot_products": "区域热门 SKU 离线统计",
        "session_analysis": "用户 Session 行为聚合分析",
        "ad_traffic_realtime": "广告展现点击实时统计",
    }
    purpose_out = (purpose or "").strip() or defaults.get(module_id, "电商行为分析")
    consent, ack = tenant_consent, compliance_acknowledged
    if role in ("super_admin", "admin"):
        consent, ack = True, True
    return purpose_out, consent, ack


def quick_run(
    preset_or_id: str,
    *,
    params: dict[str, Any] | None = None,
    tenant_id: str | None = None,
    operator_role: str | None = None,
    tenant_consent: bool = False,
    compliance_acknowledged: bool = False,
    purpose: str | None = None,
) -> dict[str, Any]:
    """实现 quick执行 的功能。
    
    :param preset_or_id: 参数 preset_or_id（类型: str）
    :param params: 参数 params（类型: dict[str, Any] | None）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param operator_role: 参数 operator_role（类型: str | None）
    :param tenant_consent: 参数 tenant_consent（类型: bool）
    :param compliance_acknowledged: 参数 compliance_acknowledged（类型: bool）
    :param purpose: 参数 purpose（类型: str | None）
    :return: 返回 dict[str, Any] 结果
    """
    module_id = resolve_module_id(preset_or_id)
    if not module_id:
        return {
            "ok": False,
            "error_code": "ANALYTICS_MODULE_UNKNOWN",
            "message_zh": ERROR_HINTS_ZH["ANALYTICS_MODULE_UNKNOWN"],
        }
    purpose_final, consent, ack = apply_run_defaults(
        module_id=module_id,
        operator_role=operator_role,
        purpose=purpose,
        tenant_consent=tenant_consent,
        compliance_acknowledged=compliance_acknowledged,
    )
    out = run_analytics_module(
        module_id,
        params=params or {},
        tenant_id=tenant_id,
        operator_role=operator_role,
        purpose=purpose_final,
        tenant_consent=consent,
        compliance_acknowledged=ack,
    )
    return enrich_result_zh(out)


def enrich_result_zh(result: dict[str, Any]) -> dict[str, Any]:
    """实现 enrich结果zh 的功能。
    
    :param result: 参数 result（类型: dict[str, Any]）
    :return: 返回 dict[str, Any] 结果
    """
    code = result.get("error_code")
    if not result.get("ok") and code:
        result = dict(result)
        result["message_zh"] = ERROR_HINTS_ZH.get(code, result.get("note") or "分析未完成")
        return result
    if result.get("ok"):
        result = dict(result)
        if result.get("human_review_required"):
            result["message_zh"] = "分析完成，指标须人工核实后再用于投放/定价决策"
        else:
            result["message_zh"] = "分析完成，可核对 job_id 或报表链接"
    return result
