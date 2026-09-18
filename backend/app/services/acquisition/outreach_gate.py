# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""开发信千人千面强制序（P1-6）。

红线：无背调 → 禁止「个性化」通道；只允许标记过的标准信。
顺序：背调（OSINT/海关/官网）→ 洞察卡 → 再写信。
"""
from __future__ import annotations

from typing import Any

RESEARCH_LEVELS = {
    "none": "未背调",
    "basic": "仅基础信息",
    "osint": "OSINT/官网背调",
    "full": "完整背调（OSINT+海关/项目证据）",
}

# 允许个性化开发信的最低背调级别
PERSONALIZED_MIN_LEVEL = "basic"
_LEVEL_RANK = {"none": 0, "basic": 1, "osint": 2, "full": 3}


def evaluate_research_gate(research_level: str = "none", note: str = "") -> dict[str, Any]:
    level = (research_level or "none").lower()
    if level not in _LEVEL_RANK:
        level = "none"
    rank = _LEVEL_RANK[level]
    personalized_ok = rank >= _LEVEL_RANK[PERSONALIZED_MIN_LEVEL]
    deep_personalized_ok = rank >= _LEVEL_RANK["osint"]
    if level == "none":
        reason = "尚未背调：禁止个性化开发信，只能发标准信且必须标记"
        next_step = "先做买家背调（公司真伪/角色/项目信号），再写个性化信"
    elif level == "basic":
        reason = "仅有基础信息：可轻度个性化（称呼+品类），禁止编造项目细节"
        next_step = "补 OSINT/海关/官网证据后可升到深度个性化"
    elif level == "osint":
        reason = "已 OSINT 背调：可引用可核验事实做个性化"
        next_step = "保持身份一致；首封外发仍需人审"
    else:
        reason = "完整背调：可深度个性化，引用必须来自背调事实"
        next_step = "首封人审后发送；持续把回复写回经验环"

    channels = {
        "standard_letter": {
            "allowed": True,
            "label": "标准开发信",
            "must_mark": level == "none",
            "hint": "无背调时必须标记「标准信/未个性化」",
        },
        "personalized_letter": {
            "allowed": personalized_ok,
            "label": "个性化开发信",
            "must_mark": False,
            "hint": "个性化必须基于背调事实，禁止编造",
        },
        "deep_personalized": {
            "allowed": deep_personalized_ok,
            "label": "深度个性化（项目/角色引用）",
            "must_mark": False,
            "hint": "引用项目、市场、角色时必须可核验",
        },
    }
    return {
        "research_level": level,
        "research_level_label": RESEARCH_LEVELS.get(level, level),
        "personalized_allowed": personalized_ok,
        "deep_personalized_allowed": deep_personalized_ok,
        "reason": reason,
        "next_step": next_step,
        "note": note or "",
        "channels": channels,
        "hint": "顺序强制：背调 → 洞察 → 写信。无背调禁用个性化发送。",
    }
