# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""COMP-03：Pro 定时市场研究服务条款（租户可见 · 已脱敏）。"""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.hermes.brand_guard import sanitize_public_copy


def build_pro_research_terms() -> dict[str, Any]:
    """build_pro_research_terms。
    :return: 返回处理结果。
    """
    monthly = int(getattr(settings, "DEERFLOW_SCHEDULE_MONTHLY_LIMIT_PER_TENANT", 4) or 4)
    plans = (getattr(settings, "DEERFLOW_SCHEDULE_PLAN_CODES", "pro,enterprise,flagship") or "").strip()
    sections = [
        {
            "id": "definition",
            "title": "服务定义",
            "body": sanitize_public_copy(
                "定时市场研究指系统按套餐配置自动排队的行业与竞品洞察任务，"
                "结果在卖货副驾中只读展示，不包含自动外发邮件、改价或部署。"
            ),
        },
        {
            "id": "ai_disclaimer",
            "title": "AI 生成内容声明",
            "body": sanitize_public_copy(
                "研究报告由 AI 辅助生成，可能存在偏差；对外使用前请人工复核事实与法规。"
                "平台不对 AI 输出导致的间接商业损失承担责任（法律强制除外）。"
            ),
        },
        {
            "id": "limits",
            "title": "使用上限",
            "body": sanitize_public_copy(
                f"默认定时额度为每租户每月 {monthly} 次（适用套餐：{plans}）。"
                "超额任务可能延迟或需升级套餐；可在租户设置中关闭定时研究。"
            ),
        },
        {
            "id": "privacy",
            "title": "数据与隐私",
            "body": sanitize_public_copy(
                "研究输入仅用于本租户洞察，不向其他租户共享；可选第三方双写仅在平台配置时生效。"
            ),
        },
    ]
    return {
        "version": "2026-06-02",
        "doc_ref": "docs/compliance/comp-03-pro-research-service-terms-memo.md",
        "monthly_limit_per_tenant": monthly,
        "plan_codes": [p.strip() for p in plans.split(",") if p.strip()],
        "sections": sections,
    }
