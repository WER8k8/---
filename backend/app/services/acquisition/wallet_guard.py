# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Token 钱包 / 三轨闸 — 诚实状态查询。

契约：
    · 无账本：unknown，hard_block_enabled=False，不编造余额
    · 余额为 0 且硬拦开启：hard_block_enabled=True + 大白话
    · 余额充足：hard_block_enabled=False
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def check_wallet_status(tenant_id: str) -> dict[str, Any]:
    """查询租户 Token/套餐状态。未接 ledger 时诚实 unknown。"""
    tenant_id = (tenant_id or "").strip() or "unknown"
    # 预留：token_ledger / plan_gate / wallet 服务
    try:
        # 生产应读 PG token_ledger + plan；当前未接线 → unknown
        has_ledger = False
        if not has_ledger:
            return {
                "tenant_id": tenant_id,
                "token_balance": None,
                "plan": None,
                "hard_block_enabled": False,
                "status": "unknown",
                "message": "计费账本尚未接入本工作区；不会误拦任务，也不会显示虚假余额。",
                "next_step": "配置 PG 与 token_ledger 后开启硬拦（余额 0 → 402）",
            }
    except Exception as exc:  # noqa: BLE001
        logger.exception("wallet_guard 查询失败 tenant=%s", tenant_id)
        return {
            "tenant_id": tenant_id,
            "token_balance": None,
            "plan": None,
            "hard_block_enabled": False,
            "status": "error",
            "message": f"查询失败：{exc}",
            "next_step": "检查后端依赖",
        }
    return {
        "tenant_id": tenant_id,
        "token_balance": None,
        "plan": None,
        "hard_block_enabled": False,
        "status": "unknown",
        "message": "无账本数据",
        "next_step": "",
    }
