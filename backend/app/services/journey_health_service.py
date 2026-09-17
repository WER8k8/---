# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户旅程健康度 — PM / 数据 / 用研可读的缺口诊断（非 mock 分数）。"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from app.services.onboarding_progress_service import (
    build_onboarding_roadmap,
    refresh_onboarding_checklist,
)
from app.services.trade_intel_service import DISCLAIMER as TRADE_INTEL_DISCLAIMER

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.tenant import Tenant

# 主链必做（不含 optional）
_CRITICAL_KEYS = (
    "site",
    "platforms",
    "publish",
    "inquiry_im",
    "wecom_push",
    "douyin_worker",
)

_ROLE_LABELS = {
    "pm": "产品经理",
    "marketing": "营销",
    "strategy": "策略",
    "market_research": "市场调研",
    "user_research": "用户研究",
    "data_analytics": "数据分析",
    "ux_research": "体验研究",
    "ui_design": "界面设计",
}

def _safe_settings(raw: Any) -> dict[str, Any]:
    """_safe_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    import json
    if not raw:
        return {}
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}

def build_journey_health(db: Session, tenant: Tenant) -> dict[str, Any]:
    """基于真实清单状态计算健康度与分角色建议。"""
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    checklist = refresh_onboarding_checklist(
        db,
        tenant,
        onboarding.get("checklist") if isinstance(onboarding.get("checklist"), list) else None,
    )
    roadmap = build_onboarding_roadmap(db, tenant, checklist)
    by_key = {str(i.get("key")): i for i in checklist if i.get("key")}
    done = sum(1 for i in checklist if i.get("status") == "done")
    total = len(checklist) or 1
    critical = [by_key[k] for k in _CRITICAL_KEYS if k in by_key]
    critical_done = sum(1 for i in critical if i.get("status") == "done")
    critical_total = len(critical) or 1
    gaps = [
        {
            "key": i.get("key"),
            "title": i.get("title"),
            "detail": i.get("detail"),
            "route": i.get("route"),
            "phase": i.get("phase"),
            "status": i.get("status"),
        }
        for i in checklist
        if i.get("status") != "done" and not i.get("optional")
    ]
    sales_gaps = [g for g in gaps if g.get("key") in ("inquiry_im", "wecom_push", "douyin_worker")]
    score_pct = round(critical_done / critical_total * 100)
    role_insights: list[dict[str, str]] = []
    if sales_gaps:
        role_insights.append(
            {
                "role": "pm",
                "insight": f"主链还差 {len(sales_gaps)} 步销售通知（5a/5b/5c），客户留言可能进系统但销售收不到。",
                "action": "优先完成企微推送与抖音评论链",
            }
        )
        role_insights.append(
            {
                "role": "marketing",
                "insight": "对外可说「AI 建站+多平台分发」；销售通知未配齐前勿承诺「自动接单」。",
                "action": "话术与系统菜单对齐《代理一页纸》",
            }
        )

    jtbd_items, jtbd_open = _build_journey_role_insights(critical_done, critical_total, done, gaps, role_insights, score_pct, tenant, total)
    next_action = None
    if gaps:
        g0 = gaps[0]
        next_action = {
            "title": g0.get("title"),
            "route": g0.get("route") or "/client/onboarding",
            "reason": g0.get("detail") or "完成此项后主链更完整",
        }

    return {
        "score_pct": score_pct,
        "checklist_done": done,
        "checklist_total": total,
        "critical_done": critical_done,
        "critical_total": critical_total,
        "roadmap_phases": len(roadmap),
        "gaps": gaps[:12],
        "sales_channel_gaps": sales_gaps,
        "jtbd_checklist": jtbd_items,
        "jtbd_gaps": jtbd_open[:4],
        "next_action": next_action,
        "role_insights": role_insights,
        "role_labels": _ROLE_LABELS,
        "data_notes": {
            "trade_intel_disclaimer": TRADE_INTEL_DISCLAIMER,
            "funnel_hint": "待处理询盘 → 带手机号 → 候选客户 → 开发信草稿 → 已发布",
        },
    }

def _build_journey_role_insights(critical_done, critical_total, done, gaps, role_insights, score_pct, tenant, total):
    """按缺口拼装分角色建议，返回 (jtbd_items, jtbd_open)。"""
    _append_wecom_research_insight(gaps, role_insights)
    _append_platform_strategy_insight(gaps, role_insights)
    jtbd_items, jtbd_open = _append_jtbd_insights(tenant, role_insights)
    _append_progress_metric_insights(critical_done, critical_total, done, score_pct, total, role_insights)
    return (jtbd_items, jtbd_open)


def _append_wecom_research_insight(gaps, role_insights):
    """企微缺口时追加用户研究视角的建议（5b 未完成）。"""
    if any(g.get("key") == "wecom_push" for g in gaps):
        role_insights.append(
            {
                "role": "user_research",
                "insight": "工厂老板常以为「留了电话就行」；需强调销售手机还要单独配企微。",
                "action": "开通向导与 IM 页重复提示 5b",
            }
        )


def _append_platform_strategy_insight(gaps, role_insights):
    """平台/首发缺口时追加策略视角的建议（曝光先于转化）。"""
    if any(g.get("key") in ("platforms", "publish") for g in gaps):
        role_insights.append(
            {
                "role": "strategy",
                "insight": "曝光先于转化：未绑平台/未首发时，蓝海与 SEO 数据仅作方向参考。",
                "action": "先完成「让人看见」再加大投放",
            }
        )


def _append_jtbd_insights(tenant, role_insights):
    """构建官网 JTBD 清单并追加体验/设计视角建议，返回 (jtbd_items, jtbd_open)。"""
    from app.services.onboarding_progress_service import build_jtbd_site_checklist
    jtbd_items = build_jtbd_site_checklist(tenant)
    jtbd_open = [i for i in jtbd_items if i.get("status") != "done"]
    if jtbd_open:
        role_insights.append(
            {
                "role": "ux_research",
                "insight": (
                    f"官网 JTBD 四要素还差 {len(jtbd_open)} 项"
                    f"（{jtbd_open[0].get('paradigm') or '建站'}：{jtbd_open[0].get('title')}）。"
                ),
                "action": "在站点内容补齐页完善主承诺、阶段服务与技术干货",
            }
        )
        role_insights.append(
            {
                "role": "ui_design",
                "insight": "L-Pro 首页顺序应为：主承诺 → 阶段 → 证据 → 产品 → 干货 → 单一 CTA。",
                "action": "/client/site-editor-lab",
            }
        )
    return (jtbd_items, jtbd_open)


def _append_progress_metric_insights(critical_done, critical_total, done, score_pct, total, role_insights):
    """追加数据分析/市场调研/体验/设计四个固定视角的建议。"""
    role_insights.append(
        {
            "role": "data_analytics",
            "insight": f"开户完成度 {done}/{total}；主链 {critical_done}/{critical_total}（{score_pct}%）。",
            "action": "用漏斗看「询盘→带号→发布」转化，勿单看访问量",
        }
    )
    role_insights.append(
        {
            "role": "market_research",
            "insight": "出海参谋蓝海来自公开统计与规则矩阵，非实时海关同源。",
            "action": TRADE_INTEL_DISCLAIMER[:120] + "…",
        }
    )
    role_insights.append(
        {
            "role": "ux_research",
            "insight": "工作台应 30 秒内回答：今天回谁、发什么、还差哪步开户。",
            "action": "今日待办优先询盘，其次开户缺口",
        }
    )
    role_insights.append(
        {
            "role": "ui_design",
            "insight": "避免工程词（探针、inbox、Webhook）；统一「询盘」「销售通知」「拉评论」。",
            "action": "主按钮：内容分发 / 询盘管理 / 开通向导",
        }
    )