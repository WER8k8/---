"""UserActionAnalyzePlatform 模块注册 — Spark 电商行为分析 → 本系统 Lane。

来源：https://github.com/oeljeklaus-you/UserActionAnalyzePlatform
原则：Spark/Java 外置 Sidecar；主站只读聚合结果；无 job/evidence 不落库。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ComplianceTier = Literal[
    "allowed_sidecar",
    "human_review",
    "restricted",
    "platform_blocked",
]

ProductLane = Literal[
    "growth_tools",
    "competitor_intel",
    "utm_attribution",
    "reference_only",
]


@dataclass(frozen=True)
class AnalyticsModule:
    id: str
    name: str
    upstream_module: str
    lane: ProductLane
    compliance: ComplianceTier
    summary: str
    compliance_note: str = ""
    requires_purpose: bool = True
    max_rows: int = 100


ANALYTICS_MODULES: tuple[AnalyticsModule, ...] = (
    AnalyticsModule(
        id="session_analysis",
        name="用户 Session 分析",
        upstream_module="user_session",
        lane="growth_tools",
        compliance="restricted",
        summary="访问时长、点击/下单/支付 session 聚合",
        compliance_note="含用户行为轨迹；须租户授权，禁止导出原始 user_id 批量外发",
        max_rows=50,
    ),
    AnalyticsModule(
        id="page_conversion",
        name="页面单跳转化率",
        upstream_module="page_single_jump",
        lane="growth_tools",
        compliance="allowed_sidecar",
        summary="关键页面间跳转转化率，优化落地页与独立站路径",
        max_rows=80,
    ),
    AnalyticsModule(
        id="hot_products",
        name="热门商品离线统计",
        upstream_module="hot_product_offline",
        lane="competitor_intel",
        compliance="allowed_sidecar",
        summary="区域 Top 热门 SKU，辅助选品与内容选题",
        max_rows=30,
    ),
    AnalyticsModule(
        id="ad_traffic_realtime",
        name="广告流量实时统计",
        upstream_module="ad_traffic_streaming",
        lane="utm_attribution",
        compliance="human_review",
        summary="广告展现/点击实时流，与 UTM 归因互补",
        compliance_note="须对接真实广告日志；结果须人工核对后再用于预算决策",
        max_rows=50,
    ),
)


def module_by_id(module_id: str) -> AnalyticsModule | None:
    """实现 modulebyID 的功能。
    
    :param module_id: 参数 module_id（类型: str）
    :return: 返回 AnalyticsModule | None 结果
    """
    key = (module_id or "").strip().lower()
    for m in ANALYTICS_MODULES:
        if m.id == key:
            return m
    return None


def callable_modules() -> list[AnalyticsModule]:
    """实现 callablemodules 的功能。
    
    :return: 返回 list[AnalyticsModule] 结果
    """
    return [m for m in ANALYTICS_MODULES if m.compliance != "platform_blocked"]


def registry_payload() -> dict:
    """实现 registrypayload 的功能。
    
    :return: 返回 dict 结果
    """
    return {
        "github": "https://github.com/oeljeklaus-you/UserActionAnalyzePlatform",
        "stars_approx": 1112,
        "stack": "Spark Core / Spark SQL / Spark Streaming + MySQL 报表",
        "integration": "vendor_submodule + sidecar_gateway",
        "vendor_path": "deploy/vendor/UserActionAnalyzePlatform",
        "install_script": "scripts/install-user-action-analytics-vendor.ps1",
        "compose_stack": "deploy/examples/user-action-analytics-stack.compose.yml",
        "sql_schema": "deploy/sql/user_action_analytics_schema.sql",
        "upstream_java_entry": {
            "session_analysis": "cn.edu.hust.session.UserVisitAnalyze",
        },
        "compliance_note": "上游 mock 数据在 Spark 作业内；主站须 job_id + MySQL evidence",
        "env": [
            "USER_ACTION_ANALYTICS_URL",
            "USER_ACTION_ANALYTICS_TOKEN",
            "USER_ACTION_ANALYTICS_MYSQL_DSN",
            "USER_ACTION_ANALYTICS_ALLOW_STUB",
        ],
        "items": [
            {
                "id": m.id,
                "name": m.name,
                "upstream_module": m.upstream_module,
                "lane": m.lane,
                "compliance": m.compliance,
                "summary": m.summary,
                "compliance_note": m.compliance_note,
                "requires_purpose": m.requires_purpose,
                "max_rows": m.max_rows,
                "callable": m.compliance != "platform_blocked",
            }
            for m in ANALYTICS_MODULES
        ],
    }
