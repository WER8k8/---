# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P0-9 — 销售漏斗权威状态机（单一事实来源 + 阶段退出标准）。

背景：此前 update_inquiry_status 仅做「状态白名单」校验（_VALID_INQUIRY_STATUSES），
允许任意状态互跳（如 closed 直接跳回 quoted、archived 跳回 in_progress），
漏斗数据失真、无法用于转化分析。

本模块定义：
- 规范化阶段顺序（pending 是 new 的别名）
- 前进-only 流转规则 + 显式「重开」例外（任意 → new）
- 每个阶段的「退出标准」（语义前置，供前端/运营参考）
- can_transition() 守卫，供路由层调用

旧三套状态机（内容发布 state_machine、ProspectLead 的 LeadStatus）保持不变，本机
仅约束 inquiries.status 这一销售漏斗主线。
"""
from __future__ import annotations

from typing import Optional

# 规范阶段顺序（漏斗主线）
FUNNEL_STAGES: list[str] = [
    "new",          # 新询盘（pending 的规范化别名）
    "in_progress",  # 销售已接手
    "quoted",       # 已报价
    "accepted",     # 买家确认/达成意向
    "processing",   # 履约/生产/交付中
    "resolved",     # 需求闭环
    "closed",       # 成功关闭
    "archived",     # 无效/放弃归档
]

# 别名归一
_ALIASES: dict[str, str] = {"pending": "new"}

# 阶段退出标准（离开该阶段、进入下一阶段前应满足的前置）
STAGE_EXIT_CRITERIA: dict[str, str] = {
    "new": "已收到询盘并完成联系方式校验（手机/邮箱至少一项）",
    "in_progress": "销售已接手并与买家建立首次有效沟通",
    "quoted": "已生成并发送正式报价单（Quote 落库）",
    "accepted": "买家确认报价或达成合作意向",
    "processing": "进入履约/生产/交付流程，生成订单或任务",
    "resolved": "询盘需求已闭环（成单或明确放弃）",
    "closed": "成功成单并关闭",
    "archived": "判定为无效/重复/放弃线索并归档",
}

TERMINAL_STATES = {"closed", "archived"}


def normalize(status: str) -> str:
    """归一化：pending → new；未知值原样返回（交由调用方判定非法）。"""
    return _ALIASES.get((status or "").strip().lower(), (status or "").strip().lower())


def stage_index(status: str) -> int:
    """返回阶段在漏斗中的下标；未知阶段返回 -1。"""
    s = normalize(status)
    return FUNNEL_STAGES.index(s) if s in FUNNEL_STAGES else -1


def is_valid_status(status: str) -> bool:
    """状态是否为漏斗已知状态（含别名）。"""
    return normalize(status) in FUNNEL_STAGES


def next_stage(status: str) -> Optional[str]:
    """返回下一阶段；已是末态则返回 None。"""
    idx = stage_index(status)
    if idx < 0 or idx >= len(FUNNEL_STAGES) - 1:
        return None
    return FUNNEL_STAGES[idx + 1]


def can_transition(from_status: str, to_status: str) -> tuple[bool, str]:
    """守卫：判断 from_status → to_status 是否允许。

    返回 (allowed, reason)。
    - 同状态：允许（no-op）
    - 重开：任意状态 → new 允许
    - 前进：to 在漏斗中位于 from 之后，允许
    - 其它（后退/跨跳）：拒绝
    """
    f = normalize(from_status)
    t = normalize(to_status)
    if f not in FUNNEL_STAGES or t not in FUNNEL_STAGES:
        return False, f"未知状态: {to_status}"
    if f == t:
        return True, "状态未变更"
    # 重开例外
    if t == "new":
        return True, "允许重开为 new（重新激活线索）"
    # 仅允许向前推进
    if stage_index(t) > stage_index(f):
        return True, f"允许向前推进: {f} → {t}"
    return False, f"不允许从 {f} 回退/跨跳至 {t}（仅允许重开为 new）"


def exit_criteria(status: str) -> str:
    """返回某阶段的退出标准说明（文档/前端提示用）。"""
    return STAGE_EXIT_CRITERIA.get(normalize(status), "")
