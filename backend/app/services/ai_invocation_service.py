# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一 AI 调用：场景解析、引擎调用、用量落库、降级。"""

from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.ai_config_service import AIConfigService
from app.services.ai_engine import get_ai_engine
from app.services.nvidia_scenario_service import (
    _get_nvidia_provider,
    get_scenario_mappings,
    resolve_scenario_model,
)

logger = logging.getLogger(__name__)

SCENARIO_ALIASES: dict[str, str] = {
    "general": "inference",
    "chat": "inference",
    "seo": "article",
    "optimize": "article",
    "video-script": "article_to_video_script",
    "video_script": "article_to_video_script",
    "rewrite": "article",
    "wiki": "article",
    "seo_matrix": "article",
    "hermes_tech_radar": "logic",
    "hermes_ecc_review": "logic",
    "hermes_patrol_summary": "logic",
}

# RADAR-07 / AI-03：Hermes 运维专用场景 → 模型族（lane=ops 时优先 logic/code）
OPS_SCENARIO_MAP: dict[str, str] = {
    "hermes_tech_radar": "logic",
    "hermes_ecc_review": "logic",
    "hermes_patrol_summary": "logic",
    "code": "code",
    "logic": "logic",
}

SCENARIO_FALLBACK_CHAIN: dict[str, list[str]] = {
    "article": ["inference"],
    "article_to_video_script": ["article", "inference"],
    "code": ["inference"],
    "logic": ["code", "inference"],
    "vision": ["inference"],
    "video_understanding": ["inference"],
}

# AI-03：运维 vs 租户客面场景分流（Hermes/ECC 走 ops，副驾/SEO 走 customer）
LANE_OPS = "ops"
LANE_CUSTOMER = "customer"
OPS_SCENARIO_DEFAULT = "code"
CUSTOMER_SCENARIO_DEFAULT = "inference"


def resolve_lane_scenario(scenario: str, *, lane: str | None = None) -> str:
    """lane=ops → 优先 code；lane=customer → 禁止 Hermes 专用 code 降级到 inference。"""
    norm = normalize_scenario(scenario)
    if lane == LANE_OPS:
        if norm in OPS_SCENARIO_MAP:
            return OPS_SCENARIO_MAP[norm]
        if norm in ("inference", "article", "article_to_video_script"):
            return OPS_SCENARIO_DEFAULT
        return norm
    if lane == LANE_CUSTOMER:
        if norm == OPS_SCENARIO_DEFAULT and scenario not in ("code",):
            return CUSTOMER_SCENARIO_DEFAULT
    return norm


def normalize_scenario(scenario: str | None, fallback: str = "inference") -> str:
    """normalize_scenario。

    参数说明：
    :param scenario: 参数 scenario
    :param fallback: 参数 fallback
    :return: 返回处理结果。
    """
    raw = (scenario or fallback).strip()
    return SCENARIO_ALIASES.get(raw, raw)


def _fallback_scenarios(primary: str) -> list[str]:
    """_fallback_scenarios。

    参数说明：
    :param primary: 参数 primary
    :return: 返回处理结果。
    """
    if not getattr(settings, "AI_SCENARIO_FALLBACK_ENABLED", True):
        return [primary]
    chain = SCENARIO_FALLBACK_CHAIN.get(primary, ["inference"])
    ordered: list[str] = [primary]
    for item in chain:
        normalized = normalize_scenario(item)
        if normalized not in ordered:
            ordered.append(normalized)
    return ordered


def get_scenario_runtime(
    db: Session | None,
    scenario: str,
    tenant_id: str | None = None,
) -> dict[str, str]:
    """返回场景运行时信息：scenario key、模型 ID、provider_id。"""
    key = normalize_scenario(scenario)
    if db is not None:
        key = resolve_scenario_model(db, key)
        mappings = get_scenario_mappings(db, tenant_id)
        model_name = mappings.get(key, key)
        provider = _get_nvidia_provider(db)
        if provider:
            return {
                "scenario": key,
                "model_name": model_name,
                "provider_id": str(provider.id),
            }
    defaults = settings.AI_NVIDIA_MODELS
    model_name = defaults.get(key, key)
    return {
        "scenario": key,
        "model_name": model_name,
        "provider_id": "env-default",
    }


def log_ai_invocation(
    db: Session | None,
    *,
    runtime: dict[str, str],
    task_type: str,
    token_usage: int = 0,
    duration_ms: int = 0,
    success: bool = True,
    error_message: str | None = None,
) -> None:
    """log_ai_invocation。

    参数说明：
    :param db: 参数 db
    :param runtime: 参数 runtime
    :param task_type: 参数 task_type
    :param token_usage: 参数 token_usage
    :param duration_ms: 参数 duration_ms
    :param success: 参数 success
    :param error_message: 参数 error_message
    :return: 返回处理结果。
    """
    if db is None or runtime.get("provider_id") == "env-default":
        return
    try:
        AIConfigService(db).log_usage(
            provider_id=runtime["provider_id"],
            model_name=runtime["model_name"],
            task_type=task_type,
            total_tokens=token_usage,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
        )
    except Exception as exc:
        logger.warning("Failed to log AI usage: %s", exc)


async def _invoke_llm_once(
    db: Session | None,
    *,
    prompt: str,
    scenario: str,
    max_tokens: int,
    task_type: str | None,
    tenant_id: str | None = None,
    max_retries: int = 3,
) -> dict[str, Any]:
    """_invoke_llm_once。

    参数说明：
    :param db: 参数 db
    :param prompt: 参数 prompt
    :param scenario: 参数 scenario
    :param max_tokens: 参数 max_tokens
    :param task_type: 参数 task_type
    :param tenant_id: 参数 tenant_id
    :param max_retries: 参数 max_retries
    :return: 返回处理结果。
    """
    runtime = get_scenario_runtime(db, scenario, tenant_id=tenant_id)
    task = task_type or runtime["scenario"]
    started = time.perf_counter()
    result: dict[str, Any] = {}
    success = False
    error_message: str | None = None
    try:
        result = await get_ai_engine().generate(
            prompt,
            model=runtime["scenario"],
            max_tokens=max_tokens,
            max_retries=max_retries,
        )
        success = True
        result["scenario"] = runtime["scenario"]
        result["model_name"] = runtime["model_name"]
        if tenant_id:
            result["tenant_id"] = tenant_id
        return result
    except Exception as exc:
        error_message = str(exc)
        raise
    finally:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        tokens = int(result.get("token_usage") or 0)
        log_ai_invocation(
            db,
            runtime=runtime,
            task_type=task,
            token_usage=tokens,
            duration_ms=elapsed_ms,
            success=success,
            error_message=error_message,
        )


async def invoke_llm(
    db: Session | None,
    *,
    prompt: str,
    scenario: str = "inference",
    max_tokens: int = 2000,
    task_type: str | None = None,
    enable_fallback: bool | None = None,
    tenant_id: str | None = None,
    max_retries: int = 3,
    lane: str | None = None,
) -> dict[str, Any]:
    """按场景调用对话模型；lane=ops|customer 分流（AI-03）。"""
    primary = resolve_lane_scenario(scenario, lane=lane)
    use_fallback = (
        settings.AI_SCENARIO_FALLBACK_ENABLED
        if enable_fallback is None
        else enable_fallback
    )
    candidates = _fallback_scenarios(primary) if use_fallback else [primary]
    last_error: Exception | None = None
    for idx, candidate in enumerate(candidates):
        try:
            result = await _invoke_llm_once(
                db,
                prompt=prompt,
                scenario=candidate,
                max_tokens=max_tokens,
                task_type=task_type,
                tenant_id=tenant_id,
                max_retries=max_retries,
            )
            if idx > 0:
                result["fallback"] = True
                result["fallback_from"] = primary
            return result
        except Exception as exc:
            last_error = exc
            logger.warning("invoke_llm scenario=%s failed: %s", candidate, exc)

    raise RuntimeError(str(last_error or "AI 调用失败"))


async def invoke_optimize(
    db: Session | None,
    *,
    content: str,
    optimization_type: str,
    keywords: list[str],
    scenario: str = "article",
    enable_fallback: bool | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """SEO/内容优化，走统一场景模型（含技术参数合规校验）。"""
    from app.services.content_optimizer import ContentOptimizer
    kw_text = ", ".join(keywords) if keywords else "无"
    type_hint = {
        "seo": "SEO 友好、关键词自然融入",
        "title": "标题（15-30字）",
        "description": "Meta 描述（50-120字）",
        "readability": "可读性与段落结构",
        "content": "正文 SEO 与可读性",
        "alt_text": "图片 Alt 文本（5-20字）",
    }.get(optimization_type, "整体质量")
    prompt = (
        f"请优化以下内容的{type_hint}。\n"
        f"目标关键词：{kw_text}\n\n"
        f"原文：\n{content}\n\n"
        "请直接输出优化后的正文，不要解释过程。"
    )
    normalized = normalize_scenario(scenario or "article")
    result = await invoke_llm(
        db,
        prompt=prompt,
        scenario=normalized,
        task_type=f"optimize:{optimization_type}",
        enable_fallback=enable_fallback,
        tenant_id=tenant_id,
    )
    text = (result.get("content") or "").strip()
    optimizer = ContentOptimizer()
    text = optimizer.restore_technical_params(content, text)
    compliance = optimizer.validate_compliance(content, text)
    return {
        "optimized_content": text,
        "changes": ["内容已按场景模型优化"],
        "token_usage": result.get("token_usage", 0),
        "cost": result.get("cost", 0),
        "technical_params_preserved": compliance.get("technical_params_preserved", True),
        "compliance": compliance,
        "scenario": result.get("scenario", normalized),
        "fallback": result.get("fallback", False),
        "model_name": result.get("model_name"),
    }
