# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P3-6 信用 / 付款风险闸 — 高风险阻断自动 PI。

原则：
    · 风险只提示/阻断自动动作，不禁止人工跟进
    · 依据：国别 Playbook、历史流失、定金缺失、风险标记 — 不编造征信分
"""
from __future__ import annotations

from typing import Any, Optional

# 高风险国别/区域提示（行业常识，需经验校准；非制裁名单替代）
HIGH_RISK_HINT_COUNTRIES = {
    "AF": "部分非洲/高风险地付款风险偏高，提高定金比例",
}
# 可放宽但仍需定金的常见区域
WATCH_COUNTRIES = {
    "IN": "印度新客首款常谈全款或高比例定金",
}


def payment_risk_gate(
    *,
    country: str = "",
    buyer_type: str = "new",
    buyer_grade: str = "",
    risk_flags: Optional[list[str]] = None,
    deposit_ratio: Optional[float] = None,
    stage: str = "",
    auto_pi: bool = False,
    ops_store: Any = None,
    inquiry_id: str = "",
    tenant_id: str = "",
) -> dict[str, Any]:
    """付款风险评估 + 自动 PI 闸门。"""
    country = (country or "").upper()[:2]
    flags = [str(x) for x in (risk_flags or [])]
    score_risk = 0
    reasons: list[str] = []

    if country in HIGH_RISK_HINT_COUNTRIES:
        score_risk += 2
        reasons.append(HIGH_RISK_HINT_COUNTRIES[country])
    if country in WATCH_COUNTRIES:
        score_risk += 1
        reasons.append(WATCH_COUNTRIES[country])

    if (buyer_type or "").lower() in ("new", "unknown", ""):
        score_risk += 1
        reasons.append("新客/类型未知：先核验公司实体与付款能力")

    grade = (buyer_grade or "").upper()
    if grade == "D":
        score_risk += 3
        reasons.append("客户评级 D：高风险，禁止自动 PI")
    elif grade == "C":
        score_risk += 1
        reasons.append("客户评级 C：低成本跟进，慎出正式 PI")

    if flags:
        score_risk += min(3, len(flags))
        reasons.append("风险标记：" + "、".join(flags[:5]))

    # 历史：同询盘曾流失因付款冲突
    if ops_store is not None and inquiry_id:
        try:
            card = ops_store.get_by_inquiry(inquiry_id)
            if card is not None:
                loss = list(getattr(card, "loss_reasons", None) or [])
                if any("付款" in r or "payment" in r.lower() for r in loss):
                    score_risk += 2
                    reasons.append("历史流失原因含付款冲突")
                pay = getattr(card, "payment", None)
                if pay is not None:
                    pi_no = getattr(pay, "pi_no", "") or ""
                    dep = float(getattr(pay, "deposit_amount", 0) or 0)
                    paid = bool(getattr(pay, "deposit_paid_at", "") or "")
                    if pi_no and dep > 0 and not paid and (stage or getattr(card, "stage", "")) not in ("new",):
                        score_risk += 1
                        reasons.append("已有 PI 且定金未到账")
        except Exception:
            pass

    if deposit_ratio is not None:
        try:
            r = float(deposit_ratio)
            if r <= 0:
                score_risk += 2
                reasons.append("定金比例 0：高风险")
            elif r < 0.2:
                score_risk += 1
                reasons.append("定金比例偏低（<20%）")
            elif r >= 0.3:
                score_risk -= 1
                if score_risk < 0:
                    score_risk = 0
                reasons.append("定金比例较安全（≥30%）")
        except Exception:
            pass

    if score_risk >= 4:
        level = "high"
        auto_pi_allowed = False
        plain = "付款风险高：禁止自动出 PI，须人工核验后再发。"
        next_action = "核验公司/付款账户；提高定金或改安全付款方式。"
    elif score_risk >= 2:
        level = "medium"
        auto_pi_allowed = False if auto_pi else True
        plain = "付款风险中等：自动 PI 建议关闭，可人工起草。"
        next_action = "写清定金条款；新客勿全款赊销。"
    else:
        level = "low"
        auto_pi_allowed = True
        plain = "付款风险较低：可按流程出 PI（仍建议写清定金）。"
        next_action = "标准 PI + 定金条款。"

    if auto_pi and not auto_pi_allowed:
        plain += " 当前请求自动 PI → 已阻断。"
        next_action = "改为人工 PI 或先降风险（定金/背调）。"

    return {
        "level": level,
        "risk_score": score_risk,
        "auto_pi_allowed": auto_pi_allowed,
        "auto_pi_blocked": bool(auto_pi and not auto_pi_allowed),
        "country": country,
        "buyer_type": buyer_type,
        "buyer_grade": grade,
        "risk_flags": flags,
        "deposit_ratio": deposit_ratio,
        "reasons": reasons,
        "plain": plain,
        "next_action": next_action,
        "hint": "风险闸只拦自动 PI，不拦人工跟进；依据可解释，不编造征信分。",
    }
