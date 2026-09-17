# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""能力路由：required_capabilities + 四维信号 → ai_engine 场景 tier。

评分维度（总纲 038 并入 Model Router）：Quality + Speed + Cost + Privacy。

解析优先级：
1. Cost 硬覆盖：预算紧张（< BUDGET_TIGHT_THRESHOLD）或显式 quality=low
   → 强制 cost_optimized（境内 DeepSeek 档，同时满足 strict 隐私）。
2. 能力映射（硬约束，总纲 §4.6）：取首个未被隐私闸门过滤的映射 tier
   （REASONING→logic 等；tier 键与 ai_engine._get_llm 场景键一致）。
3. 无能力标签且各维度均为默认值（medium/normal/standard、budget 缺省）
   → fallback_tier（保持既有行为）。
4. 四维加权评分：候选 tier 的维度画像做均值中心化后按权重求和取最大，
   平局按候选顺序取先者（确定性）。

Privacy 语义：strict 为合规硬闸门（数据不出境），仅允许境内 provider 支撑的
tier（DeepSeek 系）；standard 模式下 privacy 维度仅作低权重偏好。

TIER_PROFILES 为静态标定估计值（tier→provider 归属经 ai_engine.py 核实），
后续可由 model_call_ledger 实测延迟/成本数据再校准，勿视为实测结论。
"""

from __future__ import annotations

from typing import List, Optional

from app.services.model_gateway.capability import CAPABILITY_TO_TIER, normalize

# 预算阈值（USD/调用）：低于该值视为预算紧张，硬覆盖为成本优化档
BUDGET_TIGHT_THRESHOLD = 0.005
# 预算压力阈值：低于该值（但未达硬覆盖）时评分中提高 cost 权重
BUDGET_PRESSURE_THRESHOLD = 0.02

# 通用档评分候选（固定顺序 = 平局决胜顺序）
GENERIC_TIERS = ("general", "high_quality", "cost_optimized", "deepseek")
# 境内 provider（DeepSeek 系）支撑的 tier：privacy=strict 合规闸门白名单
DOMESTIC_TIERS = ("cost_optimized", "deepseek")

# tier → 四维画像（1-5，静态标定估计；cost/privacy 越高越省/越合规）
TIER_PROFILES: dict[str, dict[str, float]] = {
    "general":        {"quality": 3.0, "speed": 3.0, "cost": 3.0, "privacy": 2.0},
    "high_quality":   {"quality": 5.0, "speed": 2.0, "cost": 1.0, "privacy": 2.0},
    "cost_optimized": {"quality": 2.0, "speed": 3.5, "cost": 5.0, "privacy": 5.0},
    "deepseek":       {"quality": 3.5, "speed": 3.0, "cost": 4.0, "privacy": 5.0},
}

QUALITY_WEIGHTS = {"low": 0.5, "medium": 1.0, "high": 5.0}
SPEED_WEIGHTS = {"slow": 0.5, "normal": 1.0, "fast": 2.5}
PRIVACY_WEIGHTS = {"standard": 0.5, "strict": 3.0}

_DIMS = ("quality", "speed", "cost", "privacy")


def _norm_level(value: Optional[str], levels: dict, default: str) -> str:
    """维度取值归一化：未知/缺省值回落默认档，不抛错。"""
    if not isinstance(value, str):
        return default
    key = value.strip().lower()
    return key if key in levels else default


def _cost_weight(budget: Optional[float]) -> float:
    if budget is None:
        return 1.0
    return 2.0 if budget < BUDGET_PRESSURE_THRESHOLD else 1.0


def _score(tier: str, weights: dict, means: dict) -> float:
    profile = TIER_PROFILES[tier]
    return sum(weights[dim] * (profile[dim] - means[dim]) for dim in _DIMS)


def _best_scored(
    candidates: tuple,
    quality: str,
    speed: str,
    budget: Optional[float],
    privacy: str,
) -> str:
    """四维加权评分：候选集内均值中心化后加权和取最大（平局取先者）。"""
    weights = {
        "quality": QUALITY_WEIGHTS[quality],
        "speed": SPEED_WEIGHTS[speed],
        "cost": _cost_weight(budget),
        "privacy": PRIVACY_WEIGHTS[privacy],
    }
    means = {
        dim: sum(TIER_PROFILES[t][dim] for t in candidates) / len(candidates)
        for dim in _DIMS
    }
    best, best_score = candidates[0], None
    for tier in candidates:
        score = _score(tier, weights, means)
        if best_score is None or score > best_score:
            best, best_score = tier, score
    return best


class ModelRouter:
    """能力标签 + 四维信号 → 引擎 tier 解析器。"""

    def __init__(self, default_tier: str = "general"):
        self.default_tier = default_tier

    def resolve_tier(
        self,
        required_capabilities: Optional[List[str]] = None,
        budget: Optional[float] = None,
        quality: str = "medium",
        speed: str = "normal",
        privacy: str = "standard",
        fallback_tier: str = "",
    ) -> str:
        caps = normalize(required_capabilities)
        quality = _norm_level(quality, QUALITY_WEIGHTS, "medium")
        speed = _norm_level(speed, SPEED_WEIGHTS, "normal")
        privacy = _norm_level(privacy, PRIVACY_WEIGHTS, "standard")

        # 1. Cost 硬覆盖：预算紧张 / 显式低质量 → 成本优化档（Quality 让位于 Cost）
        if quality == "low" or (
            budget is not None and budget < BUDGET_TIGHT_THRESHOLD
        ):
            return "cost_optimized"

        # 2. 能力映射（硬约束）：取首个未被隐私闸门过滤的映射
        for cap in caps:
            tier = CAPABILITY_TO_TIER.get(cap)
            if tier and (privacy != "strict" or tier in DOMESTIC_TIERS):
                return tier

        # 3. 无能力标签且四维全默认 → 兜底档（既有行为）
        if (
            not caps
            and budget is None
            and quality == "medium"
            and speed == "normal"
            and privacy == "standard"
        ):
            return fallback_tier or self.default_tier

        # 4. 四维加权评分：无能力标签（携带维度/预算信号），或映射被隐私闸门过滤
        candidates = DOMESTIC_TIERS if privacy == "strict" else GENERIC_TIERS
        return _best_scored(candidates, quality, speed, budget, privacy)


def resolve_tier(
    required_capabilities: Optional[List[str]] = None,
    budget: Optional[float] = None,
    quality: str = "medium",
    speed: str = "normal",
    privacy: str = "standard",
    fallback_tier: str = "general",
) -> str:
    """模块级便捷函数：能力路由 + 四维评分解析。"""
    return ModelRouter().resolve_tier(
        required_capabilities, budget, quality, speed, privacy, fallback_tier
    )
