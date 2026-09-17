# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""询盘意向评分 — 副驾 inquiry_score 与公开询盘创建共用。"""

from __future__ import annotations

import re
from typing import Any, Optional


def score_inquiry_lead(
    message: str = "",
    *,
    inquiry: Optional[dict[str, Any]] = None,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    product: Optional[str] = None,
    quantity: Optional[str] = None,
) -> dict[str, Any]:
    """score_inquiry_lead。

    参数说明：
    :param message: 参数 message
    :param inquiry: 参数 inquiry
    :param name: 参数 name
    :param phone: 参数 phone
    :param product: 参数 product
    :param quantity: 参数 quantity
    :return: 返回处理结果。
    """
    inquiry = inquiry or {}
    text = " ".join(
        str(v)
        for v in [
            message,
            inquiry.get("message"),
            inquiry.get("phone"),
            phone,
            inquiry.get("quantity"),
            quantity,
            inquiry.get("product"),
            product,
            name,
            inquiry.get("name"),
        ]
        if v
    )
    score = 35
    reasons: list[str] = []
    if re.search(r"1[3-9]\d{9}", text):
        score += 25
        reasons.append("包含手机号，可直接跟进")
    if re.search(r"(报价|价格|多少钱|询价|采购|下单)", text):
        score += 15
        reasons.append("出现报价/采购意图")
    if re.search(r"(\d+\s*(平|平方|吨|立方|米|件|套)|数量|批量)", text):
        score += 15
        reasons.append("出现数量或批量信息")
    if re.search(r"(今天|明天|本周|急|尽快|马上|现货)", text):
        score += 10
        reasons.append("出现紧急交付信号")
    if re.search(r"(随便问问|了解一下|学习|资料)", text):
        score -= 15
        reasons.append("偏了解型，短期成交信号弱")
    score = max(0, min(score, 100))
    level = "high" if score >= 70 else "medium" if score >= 45 else "low"
    next_action = {
        "high": "15 分钟内电话/企微跟进，并确认规格、数量、交付地。",
        "medium": "当天发送规格与报价区间，追问用途、数量和交付时间。",
        "low": "加入培育列表，发送选型 FAQ，不占用高优先级销售时间。",
    }[level]
    return {
        "score": score,
        "level": level,
        "reasons": reasons or ["信息不足，需补手机号、数量和用途"],
        "next_action": next_action,
        "inquiry_id": inquiry.get("id"),
        "inquiry_source": "latest_inquiry" if inquiry.get("id") else "message_only",
        "source_channel": inquiry.get("source_channel"),
    }
