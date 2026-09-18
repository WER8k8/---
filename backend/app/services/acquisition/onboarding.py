# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户 Onboarding 清单（P2-4）— 开通 5 步引导，降低「不会用」流失。

傻子都行：每步一句话 + 入口路径 + 是否已完成（按能力是否用过粗判）。
"""
from __future__ import annotations

from typing import Any, Optional

STEPS: list[dict[str, Any]] = [
    {
        "id": "step-login",
        "title": "登录租户后台",
        "path": "/client/today",
        "plain": "用 tenant 账号进自己的工作台",
        "check": "login_done",
    },
    {
        "id": "step-ops-card",
        "title": "打开获客作战台",
        "path": "/client/acquisition-ops",
        "plain": "这里看客户、跟单卡、今日待办",
        "check": "ops_opened",
    },
    {
        "id": "step-first-inquiry",
        "title": "录入/接收第一条询盘",
        "path": "/client/acquisition-ops",
        "plain": "把客户原话贴进作战台，点「建卡」",
        "check": "has_inquiry",
    },
    {
        "id": "step-dispatch",
        "title": "智能拆解一次",
        "path": "/client/acquisition-ops",
        "plain": "点「智能拆解预览」，看懂步骤再派发",
        "check": "has_dispatch",
    },
    {
        "id": "step-followup",
        "title": "记一笔跟进或打开今日待办",
        "path": "/client/acquisition-ops",
        "plain": "跟进会进 SLA 待办，逾期会提醒",
        "check": "has_touch",
    },
]


def _progress_from_store(
    *,
    has_inquiry: bool = False,
    has_dispatch: bool = False,
    has_touch: bool = False,
    has_card: bool = False,
) -> dict[str, bool]:
    return {
        "login_done": True,
        "ops_opened": True,
        "has_inquiry": has_inquiry or has_card,
        "has_dispatch": has_dispatch,
        "has_touch": has_touch,
    }


def build_onboarding(
    tenant_id: str = "demo",
    *,
    ops_store: Any = None,
    has_dispatch: bool = False,
) -> dict[str, Any]:
    """生成 Onboarding 清单。ops_store 可选：有则根据跟单卡推断完成度。"""
    has_inquiry = False
    has_touch = False
    has_card = False
    if ops_store is not None:
        try:
            cards = [
                c
                for c in getattr(ops_store, "_by_inquiry", {}).values()
                if not tenant_id or getattr(c, "tenant_id", "") in ("", tenant_id)
            ]
            has_card = len(cards) > 0
            has_inquiry = any(getattr(c, "last_summary", "") or getattr(c, "buyer_display", "") for c in cards)
            has_touch = any(getattr(c, "last_touch_at", "") for c in cards)
        except Exception:
            pass

    flags = _progress_from_store(
        has_inquiry=has_inquiry,
        has_dispatch=has_dispatch,
        has_touch=has_touch,
        has_card=has_card,
    )
    steps_out = []
    done_n = 0
    for s in STEPS:
        done = bool(flags.get(s["check"], False))
        if done:
            done_n += 1
        steps_out.append({
            **s,
            "done": done,
            "status_label": "已完成" if done else "待完成",
        })
    next_step = next((s for s in steps_out if not s["done"]), None)
    total = len(steps_out)
    plain = (
        f"开通引导 {done_n}/{total}。"
        + (f"下一步：{next_step['title']}（{next_step['plain']}）" if next_step else "五步已齐，可以开始日常跟单。")
    )
    return {
        "tenant_id": tenant_id,
        "steps": steps_out,
        "done_count": done_n,
        "total": total,
        "percent": round(done_n * 100.0 / total, 1) if total else 0,
        "next_step": next_step,
        "plain_summary": plain,
        "hint": "不会用才会流失：先走完五步，系统才能开始提醒与反哺。",
    }
