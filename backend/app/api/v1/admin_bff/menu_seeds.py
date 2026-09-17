# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""四壳菜单静态种子 — 纯数据，无 HTTP / 无 DB

对齐：
- Client 四支柱 · pm-four-pillars-top12-route-map.md
- Platform 送检鉴定面 · stubVisibility.CERT_INSPECTION_MENU
- Agent 五栏
"""

from __future__ import annotations

from typing import List

from app.api.v1.admin_bff.shell import (
    SHELL_AGENT,
    SHELL_CLIENT,
    SHELL_OPS,
    SHELL_PARTNER,
    SHELL_PLATFORM,
)

CLIENT_SEED: List[dict] = [
    {
        "name": "ClientRoot",
        "path": "/client",
        "component": "Layout",
        "redirect": "/client/dashboard",
        "meta": {"title": "工作台", "icon": "lucide:layout-dashboard", "shell": SHELL_CLIENT, "order": 0},
        "children": [
            {
                "name": "ClientDashboard",
                "path": "dashboard",
                "component": "views/client/dashboard",
                "meta": {"title": "工作台", "icon": "lucide:layout-dashboard", "affixTab": True, "order": 0},
            },
            {
                "name": "ClientInquiries",
                "path": "inquiries",
                "component": "views/inquiries/index",
                "meta": {"title": "获客 · 询盘", "icon": "lucide:inbox", "order": 1},
            },
            {
                "name": "ClientProducts",
                "path": "products",
                "component": "views/products/index",
                "meta": {"title": "发品 · 产品", "icon": "lucide:package", "order": 2},
            },
            {
                "name": "ClientContent",
                "path": "content",
                "component": "views/content/index",
                "meta": {"title": "发品 · 内容", "icon": "lucide:file-text", "order": 3},
            },
            {
                "name": "ClientBilling",
                "path": "billing",
                "component": "views/client/billing",
                "meta": {"title": "账户 · 套餐", "icon": "lucide:credit-card", "order": 4},
            },
        ],
    }
]

_PLATFORM_GOV = [
    {"name": "PlatformDashboard", "path": "dashboard", "component": "views/admin/index", "meta": {"title": "超管工作台", "affixTab": True, "order": 0}},
    {"name": "PlatformTenants", "path": "tenants", "component": "views/admin/tenants", "meta": {"title": "租户列表", "order": 1}},
    {"name": "PlatformHierarchy", "path": "hierarchy", "component": "views/admin/hierarchy/index", "meta": {"title": "层级管理", "order": 2}},
    {"name": "PlatformAggregation", "path": "aggregation", "component": "views/admin/aggregation/index", "meta": {"title": "数据中心", "order": 3}},
    {"name": "PlatformSystemHealth", "path": "/system-health/dashboard", "component": "views/system-health/dashboard", "meta": {"title": "系统健康", "order": 4}},
    {"name": "PlatformFinance", "path": "finance", "component": "views/admin/finance/index", "meta": {"title": "商业财务", "order": 5}},
]

_PLATFORM_BIZ = [
    {"name": "PlatformProducts", "path": "/products", "component": "views/products/index", "meta": {"title": "产品管理", "order": 0}},
    {"name": "PlatformCategories", "path": "/products/categories", "component": "views/products/categories", "meta": {"title": "分类管理", "order": 1}},
    {"name": "PlatformIntlInquiries", "path": "/international/inquiries", "component": "views/international/inquiries/index", "meta": {"title": "海外询盘", "order": 2}},
    {"name": "PlatformSeoPublish", "path": "/seo-matrix/publish", "component": "views/seo-matrix/publish", "meta": {"title": "多平台发布", "order": 3}},
    {"name": "PlatformAiContent", "path": "ai-center/content", "component": "views/admin/ai-center/content", "meta": {"title": "AI 内容助手", "order": 4}},
    {"name": "PlatformTradeIntel", "path": "ai-engine/trade-intel", "component": "views/admin/ai-engine/trade-intel", "meta": {"title": "贸易情报", "order": 5}},
]

_PLATFORM_DEMO = [
    {"name": "DemoClientDashboard", "path": "/client/dashboard", "component": "views/client/dashboard", "meta": {"title": "租户工作台", "order": 0}},
    {"name": "DemoClientInquiries", "path": "/client/inquiries", "component": "views/inquiries/index", "meta": {"title": "租户询盘", "order": 1}},
    {"name": "DemoAgentPerformance", "path": "/agent/performance", "component": "views/agent/performance", "meta": {"title": "代理业绩", "order": 2}},
    {"name": "DemoAgentAccountOpening", "path": "/agent/account-opening", "component": "views/agent/account-opening", "meta": {"title": "代理开户", "order": 3}},
]

PLATFORM_SEED: List[dict] = [
    {
        "name": "PlatformRoot",
        "path": "/admin",
        "component": "Layout",
        "redirect": "/admin/dashboard",
        "meta": {"title": "平台治理", "icon": "lucide:shield", "shell": SHELL_PLATFORM, "order": 0},
        "children": [
            {
                "name": "CertPlatformGov",
                "path": "cert-gov",
                "redirect": "/admin/dashboard",
                "meta": {"title": "送检 · 平台治理", "icon": "lucide:shield", "order": 0},
                "children": _PLATFORM_GOV,
            },
            {
                "name": "CertPlatformBiz",
                "path": "cert-biz",
                "redirect": "/products",
                "meta": {"title": "送检 · 业务链", "icon": "lucide:workflow", "order": 1},
                "children": _PLATFORM_BIZ,
            },
            {
                "name": "CertMultiRole",
                "path": "cert-demo",
                "redirect": "/client/dashboard",
                "meta": {"title": "送检 · 多角色演示", "icon": "lucide:users", "order": 2},
                "children": _PLATFORM_DEMO,
            },
            {
                "name": "PlatformZones",
                "path": "platform-zones",
                "component": "views/admin/platform-zones",
                "meta": {"title": "三区与送检开关", "icon": "lucide:settings", "order": 3},
            },
        ],
    }
]

AGENT_SEED: List[dict] = [
    {
        "name": "AgentRoot",
        "path": "/agent",
        "component": "Layout",
        "redirect": "/agent/performance",
        "meta": {"title": "代理工作台", "icon": "lucide:briefcase", "shell": SHELL_AGENT, "order": 0},
        "children": [
            {"name": "AgentPerformance", "path": "performance", "component": "views/agent/performance", "meta": {"title": "首页", "icon": "lucide:home", "affixTab": True, "order": 0}},
            {"name": "AgentTraffic", "path": "traffic", "component": "views/agent/traffic-board", "meta": {"title": "客户", "icon": "lucide:users", "order": 1}},
            {"name": "AgentAccountOpening", "path": "account-opening", "component": "views/agent/account-opening", "meta": {"title": "开户", "icon": "lucide:user-plus", "order": 2}},
            {"name": "AgentCommission", "path": "commission", "component": "views/agent/commission", "meta": {"title": "佣金", "icon": "lucide:wallet", "order": 3}},
            {"name": "AgentChurnWarning", "path": "churn-warning", "component": "views/agent/churn-warning", "meta": {"title": "预警", "icon": "lucide:alert-triangle", "order": 4}},
        ],
    }
]

PARTNER_SEED: List[dict] = [
    {
        "name": "PartnerRoot",
        "path": "/partner",
        "component": "Layout",
        "redirect": "/partner/performance",
        "meta": {"title": "省代工作台", "icon": "lucide:landmark", "shell": SHELL_PARTNER, "order": 0},
        "children": [
            {"name": "PartnerPerformance", "path": "performance", "component": "views/partner/performance", "meta": {"title": "省代看板", "icon": "lucide:home", "affixTab": True, "order": 0}},
            {"name": "PartnerTraffic", "path": "traffic", "component": "views/agent/traffic-board", "meta": {"title": "流量看板", "icon": "lucide:users", "order": 1}},
            {"name": "PartnerAccountOpening", "path": "account-opening", "component": "views/agent/account-opening", "meta": {"title": "客户开户", "icon": "lucide:user-plus", "order": 2}},
            {"name": "PartnerCommission", "path": "commission", "component": "views/agent/commission", "meta": {"title": "佣金管理", "icon": "lucide:wallet", "order": 3}},
            {"name": "PartnerDailyReport", "path": "daily-report", "component": "views/agent/daily-report", "meta": {"title": "经营日报", "icon": "lucide:file-text", "order": 4}},
            {"name": "PartnerChurnWarning", "path": "churn-warning", "component": "views/agent/churn-warning", "meta": {"title": "流失预警", "icon": "lucide:alert-triangle", "order": 5}},
        ],
    }
]

OPS_SEED: List[dict] = [
    {
        "name": "OpsRoot",
        "path": "/dashboard",
        "component": "Layout",
        "redirect": "/dashboard",
        "meta": {"title": "运营", "icon": "lucide:settings", "shell": SHELL_OPS, "order": 0},
        "children": [
            {"name": "OpsDashboard", "path": "", "component": "views/dashboard/index", "meta": {"title": "运营总览", "affixTab": True}},
        ],
    }
]

SHELL_MENU_SEEDS: dict[str, List[dict]] = {
    SHELL_CLIENT: CLIENT_SEED,
    SHELL_PLATFORM: PLATFORM_SEED,
    SHELL_PARTNER: PARTNER_SEED,
    SHELL_AGENT: AGENT_SEED,
    SHELL_OPS: OPS_SEED,
}


def seeds_for_shell(shell: str) -> List[dict]:
    """seeds_for_shell。

    参数说明：
    :param shell: 参数 shell
    :return: 返回处理结果。
    """
    return SHELL_MENU_SEEDS.get(shell, CLIENT_SEED)
