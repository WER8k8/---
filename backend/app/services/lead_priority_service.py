# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P0-8 — 线索价值评分（驱动销售分配排序）。

背景：平台落地页线索此前纯 least-loaded 轮询分配，不看线索价值；高价值线索
与普通线索被无差别均摊，资深销售无法优先消化优质线索。

本模块基于「联系方式完整度 + 产品明确度 + 归因渠道质量 + 需求描述丰富度」
给出 0-100 的 priority_score，回写到 Inquiry.priority_score（迁移 117 新增列），
供分配加权与销售队列排序使用。
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry

logger = logging.getLogger(__name__)


# 归因渠道质量映射（与 utm_attribution_service._derive_attribution_channel 标准分类一致）
_CHANNEL_PRIORITY: dict[str, int] = {
    "ai_search": 25,
    "seo": 25,
    "referral": 25,
    "customer_finder": 20,
    "social": 15,
    "email": 15,
    "direct": 5,
}


def compute_inquiry_priority(db: Session, inquiry: Inquiry) -> int:
    """计算线索价值评分（0-100）。纯字段派生，不依赖外部 join。"""
    score = 0
    has_email = bool(getattr(inquiry, "email", None))
    has_phone = bool(getattr(inquiry, "phone", None))
    if has_email and has_phone:
        score += 25
    elif has_email or has_phone:
        score += 12

    product = getattr(inquiry, "product", None)
    if product:
        score += 10

    channel = (getattr(inquiry, "attribution_channel", None) or "direct").lower()
    score += _CHANNEL_PRIORITY.get(channel, 5)

    message = getattr(inquiry, "message", None) or ""
    if len(message) > 50:
        score += 10
    elif len(message) > 20:
        score += 5

    return min(score, 100)


def priority_label(score: int) -> str:
    """将评分映射为价值档位，便于前端展示。"""
    if score >= 70:
        return "A"
    if score >= 45:
        return "B"
    if score >= 25:
        return "C"
    return "D"
