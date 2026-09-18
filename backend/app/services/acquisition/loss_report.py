# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""流失原因报表（P1-3）— 按原因分布，傻子能看懂。"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

# 原因 → 大白话解读 + 建议动作
REASON_HINTS = {
    "价格高": "竞品更便宜或价值没讲清；下次用条件换让步，勿白降价",
    "认证不够": "补齐认证清单/检测报告，无证不宣称有证",
    "交期不合适": "交期写清工作日与排产前提；赶工要加价",
    "付款方式冲突": "对齐国别付款习惯；新客提高定金比例",
    "已选同行": "问清输给谁、哪一项；1–2 周后再触达",
    "无回复": "多半是资格不匹配或触达无效；优化背调与首封",
    "MOQ不合": "谈拼柜/起订量方案，或引导相邻规格",
    "其他": "写清真实原因，经验环才能反哺",
}


def _normalize_reason(reason: str) -> str:
    r = (reason or "").strip()
    if not r:
        return "其他"
    if "无回复" in r or r == "原因未知":
        return "无回复"
    return r


def build_loss_report(cards: Iterable[Any], tenant_id: str = "") -> dict[str, Any]:
    counter: Counter[str] = Counter()
    items: list[dict[str, Any]] = []
    total_lost = 0
    for card in cards:
        reasons = list(getattr(card, "loss_reasons", None) or [])
        if not reasons and getattr(card, "stage", "") != "lost":
            continue
        total_lost += 1
        norm = [_normalize_reason(r) for r in (reasons or ["其他"])]
        for r in norm:
            counter[r] += 1
        items.append({
            "inquiry_id": getattr(card, "inquiry_id", ""),
            "buyer_display": getattr(card, "buyer_display", "") or "",
            "buyer_grade": getattr(card, "buyer_grade", "") or "",
            "stage": getattr(card, "stage", ""),
            "loss_reasons": norm,
            "loss_note": getattr(card, "loss_note", "") or "",
            "lost_at": getattr(card, "lost_at", "") or "",
            "owner_user_id": getattr(card, "owner_user_id", "") or "",
        })

    total_marks = sum(counter.values()) or 1
    distribution = [
        {
            "reason": reason,
            "count": count,
            "percent": round(count * 100.0 / total_marks, 1),
            "hint": REASON_HINTS.get(reason, "结合个案复盘话术与报价结构"),
        }
        for reason, count in counter.most_common()
    ]
    top = distribution[0]["reason"] if distribution else ""
    plain = (
        f"共流失 {total_lost} 单。最常见原因是「{top}」（{distribution[0]['count'] if distribution else 0} 次）。"
        if distribution
        else "暂无流失记录，保持跟进节奏。"
    )
    return {
        "tenant_id": tenant_id,
        "total_lost": total_lost,
        "total_reason_marks": sum(counter.values()),
        "distribution": distribution,
        "items": items,
        "top_reason": top,
        "plain_summary": plain,
        "hint": "原因可多选；报表按「原因出现次数」统计，一单可贡献多条。",
    }
