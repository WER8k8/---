# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Model Gateway — 轮16 重构（总纲 §4.6）。

能力标签路由 + 成本记账门面。复用既有 get_ai_engine() 单例，不重建已存在模块。
业务只传 required_capabilities + budget，由 router 解析为 ai_engine 场景 tier；
每次调用写 model_call_ledger（最佳努力，失败不影响主链路），可汇总至 token_ledger。

默认经 settings.MODEL_GATEWAY_ENABLED 特性开关接入（默认关，零回归）。
"""

from __future__ import annotations

from app.core.config import settings
from app.services.model_gateway.capability import (
    ALL_CAPABILITIES,
    CAPABILITY_TO_TIER,
    CHEAP,
    CODING,
    FAST,
    REASONING,
    STRUCTURED_OUTPUT,
    TRANSLATION,
    VISION,
    WRITING,
    normalize,
)
from app.services.model_gateway.gateway import ModelGateway, get_model_gateway
from app.services.model_gateway.ledger import CostLedger, aggregate_to_token_ledger, ledger
from app.services.model_gateway.router import ModelRouter, resolve_tier

__all__ = [
    "REASONING",
    "CODING",
    "VISION",
    "WRITING",
    "TRANSLATION",
    "STRUCTURED_OUTPUT",
    "CHEAP",
    "FAST",
    "ALL_CAPABILITIES",
    "CAPABILITY_TO_TIER",
    "normalize",
    "ModelRouter",
    "resolve_tier",
    "CostLedger",
    "ledger",
    "aggregate_to_token_ledger",
    "ModelGateway",
    "get_model_gateway",
    "is_gateway_enabled",
]


def is_gateway_enabled() -> bool:
    """是否启用 Model Gateway（默认关，零回归）。"""
    return bool(getattr(settings, "MODEL_GATEWAY_ENABLED", False))
