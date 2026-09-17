# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""RFQ 评分服务 — 确定性规则，不可由 LLM 覆盖。

评分规则（Technical Spec §6 / Master Spec §12）：
- Project identified: +20
- Quantity known: +15
- Technical requirement: +20
- Country known: +10
- Timeline known: +10
- Company identified: +15
- Email verified: +5
- Phone: +5
总分 0-100。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


# 评分规则配置（可数据库化）
RFQ_SCORE_RULES: dict[str, int] = {
    "project_identified": 20,
    "quantity_known": 15,
    "technical_requirement": 20,
    "country_known": 10,
    "timeline_known": 10,
    "company_identified": 15,
    "email_verified": 5,
    "phone": 5,
}


def score_rfq(payload: dict[str, Any]) -> dict[str, Any]:
    """对 RFQ 提交内容进行确定性评分，返回总分与明细。

    Args:
        payload: RFQCreate 的 model_dump() 字典

    Returns:
        {"score": int, "details": [{"rule": str, "points": int, "reason": str}]}
    """
    score = 0
    details: list[dict[str, Any]] = []
    # 项目识别
    project = payload.get("project") or payload.get("project_type") or ""
    if project.strip():
        score += 20
        details.append({
            "rule": "project_identified",
            "points": 20,
            "reason": "项目已识别",
        })

    # 数量已知
    qty = payload.get("quantity")
    if qty is not None and float(qty) > 0:
        score += 15
        details.append({
            "rule": "quantity_known",
            "points": 15,
            "reason": f"数量已知: {qty} {payload.get('quantity_unit', '')}",
        })

    # 技术要求
    reqs = payload.get("requirements") or []
    if reqs:
        score += 20
        details.append({
            "rule": "technical_requirement",
            "points": 20,
            "reason": f"技术要求已提供 ({len(reqs)} 项)",
        })

    # 国家已知
    country = payload.get("country") or ""
    if country.strip():
        score += 10
        details.append({
            "rule": "country_known",
            "points": 10,
            "reason": f"目标国家: {country}",
        })

    # 交期已知
    delivery = payload.get("delivery_date") or ""
    if delivery:
        score += 10
        details.append({
            "rule": "timeline_known",
            "points": 10,
            "reason": f"期望交期: {delivery}",
        })

    # 公司已识别
    company = payload.get("company_domain") or payload.get("company") or ""
    if company.strip():
        score += 15
        details.append({
            "rule": "company_identified",
            "points": 15,
            "reason": f"公司: {company[:50]}",
        })

    # 邮箱已验证
    email = payload.get("email") or ""
    if email.strip():
        score += 5
        details.append({
            "rule": "email_verified",
            "points": 5,
            "reason": "邮箱已提供",
        })

    # 电话
    phone = payload.get("phone") or ""
    if phone.strip():
        score += 5
        details.append({
            "rule": "phone",
            "points": 5,
            "reason": "电话已提供",
        })

    return {
        "score": min(score, 100),
        "details": details,
    }


def score_to_label(score: int) -> str:
    """将 RFQ Score 映射为优先级标签。"""
    if score >= 85:
        return "Priority"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


class RFQService:
    """RFQ 报价与询盘处理服务。"""

    def __init__(self, db: Any = None):
        self.db = db

    async def create_quote(
        self,
        tenant_id: str,
        product_name: str = "",
        quantity: int = 1,
        currency: str = "USD",
        unit_price: float = 100.0,
    ) -> dict[str, Any]:
        """为特定租户生成初始询盘/报价草稿。"""
        import uuid
        quote_id = f"quote_{uuid.uuid4().hex[:8]}"
        total_amount = round(quantity * unit_price, 2)
        return {
            "id": quote_id,
            "tenant_id": tenant_id,
            "product_name": product_name,
            "quantity": quantity,
            "currency": currency,
            "total_amount": total_amount,
            "status": "draft",
        }
