# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""UBrain 对话上下文：经营快照 + 记忆，供 general LLM 与智能路由使用。"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session


def refine_intent(message: str, intent: str) -> str:
    """general 二次路由：补漏 export / 明确复盘 / 经营诊断类问题。"""
    if intent != "general":
        return intent
    m = message.strip()
    if re.search(
        r"(出口|外销).{0,12}(越南|沙特|美国|印尼|阿联酋|迪拜|墨西哥|泰国|马来|VN|SA|US|ID|AE|MX|TH|MY)",
        m,
        re.I,
    ):
        return "export_feasibility"
    if re.search(r"(本周|上周).{0,8}(线索|询盘).{0,8}(复盘|统计|报告)", m):
        return "weekly_lead_report"
    if re.search(r"^生成本周线索复盘|^本周线索复盘", m):
        return "weekly_lead_report"
    if re.search(r"(待处理|未回复).{0,6}询盘|经营.{0,4}(怎么样|如何|诊断|快照)", m):
        return "ops_snapshot"
    if re.search(r"(背调|尽调|尽职调查|OSINT|background\s*check)", m, re.I):
        return "osint_check"
    if re.search(r"(形式发票|proforma|\bPI\b|报价单)", m, re.I):
        return "proforma_invoice"
    if re.search(r"(官网分析|网站画像|ICP|分析.{0,6}官网)", m, re.I):
        return "website_icp"
    return intent


def is_strategic_question(message: str) -> bool:
    """is_strategic_question。

    参数说明：
    :param message: 参数 message
    :return: 返回处理结果。
    """
    m = message.strip()
    return bool(
        re.search(
            r"(最该|应该|优先|先做|怎么办|怎么提升|转化率|成交率|复盘|诊断|建议)",
            m,
        )
        and re.search(r"(询盘|线索|成交|订单|客户|卖货|出口|开发信)", m)
    )


def build_situational_context(
    db: Session | None,
    tenant_id: str | None,
    memory: dict[str, Any],
) -> str:
    """build_situational_context。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param memory: 参数 memory
    :return: 返回处理结果。
    """
    lines: list[str] = []
    if db is not None and tenant_id:
        try:
            from app.services.ubrain.inquiry_context_service import tenant_ops_snapshot
            snap = tenant_ops_snapshot(db, tenant_id)
            lines.append(
                "待处理询盘 "
                f"{snap.get('pending_inquiries', 0)} 条"
                f"（带手机 {snap.get('pending_with_phone', 0)} 条）"
            )
            draft = snap.get("prospects_draft_ready") or 0
            if draft:
                lines.append(f"待发送开发信草稿 {draft} 条")
            for hint in (snap.get("hints") or [])[:2]:
                lines.append(str(hint))
        except Exception:
            pass

        try:
            report = _weekly_summary(db, tenant_id)
            if report:
                lines.append(report)
        except Exception:
            pass

    fb = memory.get("last_feedback")
    if isinstance(fb, dict) and fb.get("inquiries_sample"):
        lines.append(
            f"近 {fb.get('period_days', 7)} 天线索样本 {fb.get('inquiries_sample')} 条，"
            f"带手机 {fb.get('inquiries_with_phone', 0)} 条，"
            f"已发开发信 {fb.get('prospects_outreach_sent', 0)} 条"
        )

    hints = memory.get("research_hints") or []
    if hints:
        lines.append("研究记忆：" + "；".join(str(h) for h in hints[:2]))

    cat = memory.get("product_category")
    regions = memory.get("preferred_regions") or []
    if cat:
        lines.append(f"主营品类 {cat}" + (f"，偏好市场 {'、'.join(regions[:4])}" if regions else ""))

    if not lines:
        return "- 暂无自动拉取的经营数据，请结合用户描述给出可执行建议。"
    return "\n".join(f"- {line}" for line in lines)


def _weekly_summary(db: Session, tenant_id: str) -> str:
    """_weekly_summary。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    from app.services.inquiries_unified_service import InquiriesUnifiedService
    svc = InquiriesUnifiedService(db)
    data = svc.list_page(page=1, page_size=200, tenant_id=tenant_id)
    items = data.get("items") or []
    if not items:
        return ""
    with_phone = [
        i for i in items if re.search(r"1[3-9]\d{9}", str(i.get("phone") or ""))
    ]
    return (
        f"近期线索池共 {len(items)} 条样本，带手机号 {len(with_phone)} 条"
        f"（可用于估算跟进优先级）"
    )
