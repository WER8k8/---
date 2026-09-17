"""AI 能力三件套单元测试：幻觉检测 + Prompt 注入中间件 + 意图分类。

覆盖 §14 缺口：hallucination_detector、prompt_injection_middleware，
以及通用意图 golden set（20 条）。
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, patch

from app.services.ai.hallucination_detector import fact_check
from app.core.prompt_injection_middleware import (
    PromptInjectionMiddleware,
    _PROMPT_INJECTION_PATTERNS,
    _should_run,
)


class TestHallucinationDetector:
    def test_normal_response_no_hallucination(self):
        prompt = "轻集料混凝土密度 1200kg/m3，强度等级 LC20，请生成产品描述"
        response = ("本品采用轻集料混凝土，密度为1200 kg/m³，强度等级LC20，"
                    "符合 JGJ/T 12-2019 标准，保温隔热性能优异。")
        result = fact_check(prompt, response)
        assert result["is_hallucinated"] is False
        assert result["confidence"] >= 0.5

    def test_number_drift_detected(self):
        prompt = "轻集料混凝土密度 1200kg/m3，强度等级 LC20"
        response = ("本品密度为1500 kg/m³（远高于行业标准），"
                    "强度等级达到LC30，导热系数0.25 W/m·K，"
                    "防火等级A级，售价USD 85.5/套。")
        result = fact_check(prompt, response)
        assert result["is_hallucinated"] is True
        assert result["confidence"] >= 0.4

    def test_internal_contradiction_detected(self):
        prompt = "请根据以下参数生成产品页：密度 1200kg/m3"
        response = ("该产品密度为1200 kg/m³，满足客户需求。"
                    "注：经工厂复核，实际密度应为1400 kg/m³，已更新参数。")
        result = fact_check(prompt, response)
        assert result["is_hallucinated"] is True
        assert any(kw in result["reason"] for kw in ["矛盾", "不一致"])

    def test_safe_low_confidence(self):
        prompt = "请介绍本公司轻集料混凝土产品"
        response = "轻集料混凝土是一种轻质高强建筑材料，广泛应用于建筑保温。"
        result = fact_check(prompt, response)
        assert result["is_hallucinated"] is False

    def test_empty_response_handled(self):
        result = fact_check("请问密度多少？", "")
        assert isinstance(result["is_hallucinated"], bool)
        assert isinstance(result["confidence"], float)

    def test_value_mismatch_on_key_param(self):
        prompt = "产品参数：密度 1200kg/m3，强度等级 LC20"
        response = "该材料密度达 1500 kg/m3，强度等级为 LC25，导热系数 0.22 W/mK。"
        result = fact_check(prompt, response)
        assert result["is_hallucinated"] is True
