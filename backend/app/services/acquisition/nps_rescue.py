# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P2-5 NPS / 低使用挽回 — 发布后/续费前触达；使用度低提醒。

原则：
    · 无数据不编 NPS 分数
    · 使用度低（无跟单/无跟进）→ 挽回提醒
    · 只出建议动作，不自动发骚扰消息
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def nps_and_rescue_brief(
    *,
    tenant_id: str = "demo",
    ops_store: Any = None,
    onboarding_view: Optional[dict[str, Any]] = None,
    win_loss_view: Optional[dict[str, Any]] = None,
    billing_view: Optional[dict[str, Any]] = None,
    nps_score: Optional[int] = None,
) -> dict[str, Any]:
    """综合：NPS（有则报）+ 低使用挽回建议。"""
    card_n = 0
    touch_n = 0
    won_n = 0
    lost_n = 0
    if ops_store is not None:
        try:
            cards = list(getattr(ops_store, "_by_inquiry", {}).values())
            if tenant_id:
                cards = [c for c in cards if getattr(c, "tenant_id", "") in ("", tenant_id)]
            card_n = len(cards)
            touch_n = sum(1 for c in cards if getattr(c, "last_touch_at", ""))
            won_n = sum(
                1
                for c in cards
                if getattr(c, "stage", "") == "won" or bool(getattr(c, "won_at", ""))
            )
            lost_n = sum(1 for c in cards if getattr(c, "stage", "") == "lost")
        except Exception as exc:  # noqa: BLE001
            import logging
            logging.getLogger(__name__).warning("nps rescue ops_store stats failed: %s", exc)
    if win_loss_view:
        won_n = won_n or int(win_loss_view.get("won_count") or 0)
        lost_n = lost_n or int(win_loss_view.get("lost_count") or 0)

    onb_done = 0
    onb_total = 5
    if onboarding_view:
        onb_done = int(onboarding_view.get("done_count") or 0)
        onb_total = int(onboarding_view.get("total") or 5)

    usage_low = card_n == 0 or touch_n == 0
    rescue_actions: list[str] = []
    if onb_done < onb_total:
        rescue_actions.append(f"先走完开通引导（{onb_done}/{onb_total}），不会用最容易流失")
    if card_n == 0:
        rescue_actions.append("录入第一条询盘，打开获客作战台试跑")
    elif touch_n == 0:
        rescue_actions.append("给已有客户记一笔跟进，激活今日待办")
    if won_n == 0 and lost_n == 0:
        rescue_actions.append("成交或流失后登记原因，经验环才能反哺")
    if billing_view and (billing_view.get("balance") is None):
        rescue_actions.append("计费账本未接入时余额不可见，可先完成联调配置")

    # NPS：仅在外部传入分数时展示，不编造
    nps_block: dict[str, Any]
    if nps_score is None:
        nps_block = {
            "score": None,
            "collected": False,
            "label": "尚未收集",
            "plain": "NPS 尚未收集；可在续费前或关键节点发一次满意度调查。",
            "suggested_touch": "续费前 7 天 / 成交后 3 天 发一次 1 题 NPS（0–10）",
        }
    else:
        s = max(0, min(10, int(nps_score)))
        if s >= 9:
            bucket, label = "promoter", "推荐者"
        elif s >= 7:
            bucket, label = "passive", "中立"
        else:
            bucket, label = "detractor", "贬损者"
        nps_block = {
            "score": s,
            "collected": True,
            "bucket": bucket,
            "label": label,
            "plain": f"NPS {s} 分（{label}）。" + (
                "可邀请转介绍。" if bucket == "promoter"
                else "中立：重点补体验与响应速度。" if bucket == "passive"
                else "偏低：优先回访失败原因，暂停推销。"
            ),
            "suggested_touch": "贬损者 48h 内人工回访；推荐者可请案例/转介绍",
        }

    if usage_low and not rescue_actions:
        rescue_actions.append("使用度低：建议本周至少完成 1 次跟进或派发")

    plain = (
        f"NPS：{nps_block['plain']} "
        f"使用度：跟单卡 {card_n}，有跟进 {touch_n}。"
        + ("需要挽回提醒。" if usage_low else "使用节奏正常。")
    )
    return {
        "tenant_id": tenant_id,
        "nps": nps_block,
        "usage": {
            "cards": card_n,
            "touches": touch_n,
            "won": won_n,
            "lost": lost_n,
            "onboarding_done": onb_done,
            "onboarding_total": onb_total,
            "usage_low": usage_low,
        },
        "rescue_actions": rescue_actions,
        "should_notify": bool(usage_low or (nps_block.get("collected") and nps_block.get("bucket") == "detractor")),
        "plain_summary": plain,
        "hint": "挽回只出建议动作，不自动群发；NPS 无分数不编造。",
        "generated_at": _now(),
    }
