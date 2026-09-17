# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Model Gateway 门面（总纲 §4.6）。

复用既有 get_ai_engine() 单例，不重建已存在模块；新增能力标签路由 + 成本记账。
业务只传 required_capabilities + budget；返回结构与 ai_engine.generate() 一致
（{content, token_usage, cost, model}），保证下游（旺财 N4 等）零改动接入。

每次调用最佳努力写入 model_call_ledger（失败不影响主链路，总纲 禁止假交付：仅旁路记录）。
保留 MVP_LAUNCH mock 门：底层 ai_engine 在 mock 模式下仍返回 stamp_mock 标记载荷，
gateway 透传，不篡改 mode 标记。
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.services.model_gateway.capability import normalize
from app.services.model_gateway.ledger import CostLedger
from app.services.model_gateway.router import resolve_tier


class ModelGateway:
    """能力路由 + 成本记账门面。"""

    def __init__(self, ledger: Optional[CostLedger] = None):
        self._ledger = ledger or CostLedger()

    async def generate(
        self,
        prompt: str,
        *,
        required_capabilities: Optional[List[str]] = None,
        budget: Optional[float] = None,
        quality: str = "medium",
        speed: str = "normal",
        privacy: str = "standard",
        model: Optional[str] = None,
        max_tokens: int = 1000,
        task_complexity: str = "medium",
        max_retries: int = 3,
        tenant_id: Optional[str] = None,
        task_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """兼容 ai_engine.generate 的门面。

        - model 优先（显式 tier）；否则由 required_capabilities + budget
          + quality/speed/privacy 四维信号经 router 解析 tier。
        - 实际调用仍走 get_ai_engine()（复用，不重建）。
        - 调用明细最佳努力写入 model_call_ledger（失败不影响主链路）。
        """
        from app.services.ai_engine import get_ai_engine  # noqa: PLC0415

        tier = model or resolve_tier(
            required_capabilities,
            budget,
            quality=quality,
            speed=speed,
            privacy=privacy,
            fallback_tier="general",
        )
        cap_tag = normalize(required_capabilities)[0] if required_capabilities else None
        start = time.time()
        try:
            result = await get_ai_engine().generate(
                prompt,
                model=tier,
                max_tokens=max_tokens,
                task_complexity=task_complexity,
                max_retries=max_retries,
            )
        except Exception as exc:  # noqa: BLE001
            latency_ms = int((time.time() - start) * 1000)
            await self._ledger.record_async(
                self._ledger.build_entry(
                    tenant_id=tenant_id,
                    task_id=task_id,
                    provider=None,
                    model_name=tier,
                    capability_tag=cap_tag,
                    total_tokens=0,
                    cost_usd=0.0,
                    latency_ms=latency_ms,
                    status="failure",
                    error_message=str(exc)[:500],
                    request_id=request_id,
                    metadata=metadata,
                )
            )
            raise

        latency_ms = int((time.time() - start) * 1000)
        usage = result.get("token_usage") or 0
        cost = result.get("cost") or 0.0
        await self._ledger.record_async(
            self._ledger.build_entry(
                tenant_id=tenant_id,
                task_id=task_id,
                provider=result.get("model"),
                model_name=result.get("model") or tier,
                capability_tag=cap_tag,
                prompt_tokens=0,
                completion_tokens=usage,
                total_tokens=usage,
                cost_usd=cost,
                latency_ms=latency_ms,
                status="success",
                request_id=request_id,
                metadata=metadata,
            )
        )
        # 轮23：成功路径 ai_generation 计量旁路（TASK_CONTROL_ENABLED 默认关）。
        # 与 model_call_ledger→token_ledger 聚合二选一启用，避免双重扣减。
        if _task_meter_enabled():
            from app.services.billing.meter_event import (  # noqa: PLC0415
                emit_ai_generation_best_effort,
            )

            await emit_ai_generation_best_effort(
                tenant_id=tenant_id,
                token_delta=int(usage or 0),
                cost_usd=float(cost or 0.0),
                model_name=result.get("model") or tier,
                source_ref_id=task_id,
                event_key=f"model_gateway:{request_id}" if request_id else None,
                metadata={
                    "capability": cap_tag,
                    "tier": tier,
                    "latency_ms": latency_ms,
                },
            )
        return result


def _task_meter_enabled() -> bool:
    """TASK_CONTROL_ENABLED 懒读取（开关默认关；读取故障按关处理）。"""
    try:
        from app.core.config import settings  # noqa: PLC0415

        return bool(getattr(settings, "TASK_CONTROL_ENABLED", False))
    except Exception:  # noqa: BLE001
        return False


_GATEWAY: Optional["ModelGateway"] = None


def get_model_gateway() -> "ModelGateway":
    """获取 Model Gateway 单例。"""
    global _GATEWAY
    if _GATEWAY is None:
        _GATEWAY = ModelGateway()
    return _GATEWAY
