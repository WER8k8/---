# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""幻觉检测器：纯规则引擎，无网络依赖。

检测维度：
1. 关键词一致性 —— response 中的专有名词/数字能否在 prompt 中找到依据
2. 自我矛盾检测 —— 同一实体在 response 前后出现不同取值
"""

from __future__ import annotations

import re
from typing import Set


# ── 常量 ──────────────────────────────────────────────────────────────
_CONFIDENCE_THRESHOLD: float = 0.6

_SPEC_NAME_RE: re.Pattern = re.compile(
    r"(?<!\w)[A-Z][a-z]+(?:[A-Z][a-z]+)+|\d{4}[A-Z]{2,}"
)
_CN_ENTITIES_RE: re.Pattern = re.compile(r"[\u4e00-\u9fff]{2,}")

_NUM_CONTEXT_KEYWORDS: Set[str] = {
    "价格", "成本", "单价", "总价", "总价",
    "密度", "强度", "导热", "防火", "等级",
    "price", "cost", "unit price", "total price", "density",
    "strength", "thermal", "conductivity", "fire", "rating",
    "weight", "thickness", "area", "volume",
}


def _extract_numbers(text: str) -> Set[str]:
    """提取文本中的所有数字字符串。"""
    return set(re.findall(r"\b\d+(?:\.\d+)?\b", text))


def _extract_entities(text: str) -> Set[str]:
    """提取文本中的关键实体（中文词汇、英文复合词）。"""
    en = set(_SPEC_NAME_RE.findall(text))
    cn = set(_CN_ENTITIES_RE.findall(text))
    cn = {t for t in cn if len(t) >= 2}
    return en | cn


def _extract_number_context_pairs(text: str) -> list:
    """提取 '实体-数值' 配对，如 ('密度', '1200')。

    支持两类语序：
    - 关键词在前：密度 1200 / 密度为 1200 / 密度: 1200
    - 数值在前：1200 的密度
    中间允许常见的中文连接词（为/是/达/约/在/左右/最高），使
    '密度为1200' 与 '实际密度应为1400' 这类表述也能被配对。
    """
    pairs: list = []
    connector = r"(?:为|是|达到|达|约|在|最高|左右|应|应为|实际)?"
    for kw in _NUM_CONTEXT_KEYWORDS:
        e = re.escape(kw)
        pat = rf"{e}\s*{connector}\s*[:：＝=]?\s*(\d+(?:\.\d+)?)"
        for m in re.finditer(pat, text):
            pairs.append((kw, m.group(1)))
        pat2 = rf"(\d+(?:\.\d+)?)\s*(?:kg|W/m|℃|°C|USD|¥|元|吨|个|套|pcs|m3|m³)?\s*(?:的|.{0,0})\s*{e}"
        for m in re.finditer(pat2, text):
            pairs.append((kw, m.group(1)))
    return pairs


def fact_check(prompt: str, response: str) -> dict:
    """检测 AI response 是否存在幻觉。

    参数:
        prompt: 用户原始输入 prompt
        response: AI 模型返回的 response

    返回:
        {is_hallucinated: bool, reason: str, confidence: float}
    """
    prompt_lower = prompt.lower()
    response_lower = response.lower()

    issues: list = []

    # 检测1：响应中的数字是否在 prompt 中有依据
    prompt_nums = _extract_numbers(prompt)
    resp_nums = _extract_numbers(response)
    ungrounded_nums = resp_nums - prompt_nums
    harmless = {"0", "1", "2", "3", "2024", "2025", "2026"}
    ungrounded_nums -= harmless
    if ungrounded_nums:
        sample = sorted(ungrounded_nums)[:3]
        issues.append(
            (f"数字漂移：response 出现未在 prompt 中提及的数字 {sample}", 0.35)
        )

    # 检测2：实体-数值配对漂移
    prompt_pairs = _extract_number_context_pairs(prompt)
    resp_pairs = _extract_number_context_pairs(response)
    prompt_pair_dict: dict = {k: v for k, v in prompt_pairs}
    resp_pair_dict: dict = {k: v for k, v in resp_pairs}

    for key, val_resp in resp_pair_dict.items():
        val_prompt = prompt_pair_dict.get(key)
        if val_prompt is not None and val_resp != val_prompt:
            issues.append(
                (f"数值不一致：prompt 中'{key}'为{val_prompt}，response 改写为{val_resp}", 0.7),
            )
        elif val_prompt is None:
            issues.append(
                (f"无中生有：response 新增了'{key}'={val_resp}，prompt 未提及此参数", 0.5),
            )

    # 检测3：响应中出现了 prompt 没有的专有名词
    prompt_entities = _extract_entities(prompt)
    resp_entities = _extract_entities(response)
    new_entities = resp_entities - prompt_entities
    stop_words = {
        "产品", "公司", "我们", "您的", "标准", "质量", "服务",
        "product", "company", "we", "your", "standard", "quality",
        "service", "specification", "specifications", "spec",
        "price", "cost", "delivery", "shipping", "payment",
    }
    new_entities -= stop_words
    if len(new_entities) >= 2:
        sample = list(new_entities)[:3]
        issues.append(
            (f"引入新实体：response 包含 prompt 未提及的专有名词 {sample}", 0.25),
        )

    # 检测4：自我矛盾 —— 同一关键词两次出现给出不同数值
    all_resp_pairs = _extract_number_context_pairs(response)
    seen: dict = {}
    contradictions: list = []
    for kw, val in all_resp_pairs:
        if kw in seen and seen[kw] != val:
            contradictions.append(f"'{kw}': 先说{seen[kw]}后改{val}")
        seen[kw] = val
    if contradictions:
        issues.append(
            (f"内部自相矛盾：{'；'.join(contradictions[:2])}", 0.7),
        )

    # 综合打分
    if not issues:
        return {
            "is_hallucinated": False,
            "reason": "未发现幻觉迹象",
            "confidence": 0.95,
        }

    total_weight = sum(w for _, w in issues)
    max_weight = max(w for _, w in issues)
    confidence = min(1.0, max_weight + total_weight * 0.3)
    reason = "; ".join(r for r, _ in issues[:2])

    is_hallucinated = confidence >= _CONFIDENCE_THRESHOLD
    return {
        "is_hallucinated": is_hallucinated,
        "reason": reason,
        "confidence": round(confidence, 2),
    }
