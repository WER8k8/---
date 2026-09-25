# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""CRM 商机阶段唯一真源（W1 · N-3 / P0-8 收敛）。

背景：此前 CRM 阶段存在四套互相冲突的词表
（``crm_pipeline`` 路由 / ``opportunity`` 路由 / ``opportunity`` 模型自由串
/ ``goodjob.native_fulfillment``），导致同一商机在不同入口被写成不同阶段。

唯一裁定（见 ``docs/获客闭环唯一数据契约-2026-09-25.md`` §3.2）：

    Lead → Qualified → Contacted → Engaged → RFQ → Quote → Negotiation → Won / Lost

本模块是该词表的**唯一**定义处；任何其它模块**不得**再自建阶段字符串，
需从本模块导入 ``STAGE_ORDER`` / ``normalize_crm_stage``。
"""

from __future__ import annotations

from typing import Optional

# 唯一合法阶段集（顺序即管道顺序）
STAGE_ORDER: list[str] = [
    "Lead", "Qualified", "Contacted", "Engaged",
    "RFQ", "Quote", "Negotiation", "Won", "Lost",
]

# 中文标签
STAGE_LABELS: dict[str, str] = {
    "Lead": "线索",
    "Qualified": "已验证",
    "Contacted": "已联系",
    "Engaged": "深度沟通",
    "RFQ": "询价",
    "Quote": "报价",
    "Negotiation": "谈判",
    "Won": "赢单",
    "Lost": "输单",
}

# 各阶段赢单概率（0-1，用于加权金额）
STAGE_PROBABILITY: dict[str, float] = {
    "Lead": 0.05,
    "Qualified": 0.10,
    "Contacted": 0.20,
    "Engaged": 0.30,
    "RFQ": 0.45,
    "Quote": 0.60,
    "Negotiation": 0.75,
    "Won": 1.00,
    "Lost": 0.00,
}

# 终态
TERMINAL_STAGES = frozenset({"Won", "Lost"})

# 新建商机的初始阶段（与 ``app.models.opportunity.Opportunity.stage`` 默认值一致）
INITIAL_STAGE: str = "Lead"

# 别名 / 遗留词表 → 唯一合法阶段。
# 覆盖 P0-8（``prospecting``）与 N-3（``Quotation`` / ``new`` 等自由串）。
_LEGACY_STAGE_ALIASES: dict[str, str] = {
    "new": INITIAL_STAGE,
    "prospecting": INITIAL_STAGE,
    "lead": INITIAL_STAGE,
    "qualification": "Qualified",
    "qualified": "Qualified",
    "contacted": "Contacted",
    "engaged": "Engaged",
    "needs_analysis": "Engaged",
    "rfq": "RFQ",
    "quotation": "Quote",
    "quote": "Quote",
    "proposal": "Quote",
    "quoted": "Quote",
    "negotiation": "Negotiation",
    "negotiated": "Negotiation",
    "won": "Won",
    "lost": "Lost",
}

# 供迁移 / 校验使用的“遗留值 → 合法值”完整映射（含大小写规范）
LEGACY_STAGE_MAP: dict[str, str] = dict(_LEGACY_STAGE_ALIASES)


def normalize_crm_stage(value: Optional[str]) -> Optional[str]:
    """把任意阶段输入归一为 :data:`STAGE_ORDER` 中的合法值。

    与“兜底默认值”解耦：本函数**不**提供默认值，未知/空输入返回 ``None``，
    由调用方决定是拒绝（如 ``update_opportunity`` 返回 400）还是兜底
    （如新建商机回落 ``INITIAL_STAGE``）。

    Args:
        value: 任意阶段字符串（可为 ``None``）。

    Returns:
        规范化后的合法阶段；无法识别时返回 ``None``。
    """
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    # 1) 已经是合法值 → 原样返回（保证规范拼写）
    if raw in STAGE_ORDER:
        return raw
    # 2) 命中别名表（大小写不敏感）
    low = raw.lower()
    mapped = _LEGACY_STAGE_ALIASES.get(low)
    if mapped is not None:
        return mapped
    # 3) 与合法值仅大小写不同 → 归一
    for stage in STAGE_ORDER:
        if stage.lower() == low:
            return stage
    return None


__all__ = [
    "STAGE_ORDER",
    "STAGE_LABELS",
    "STAGE_PROBABILITY",
    "TERMINAL_STAGES",
    "INITIAL_STAGE",
    "LEGACY_STAGE_MAP",
    "normalize_crm_stage",
]
