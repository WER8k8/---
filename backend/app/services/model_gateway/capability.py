"""能力标签（总纲 §4.6）：reasoning/coding/vision/writing/translation/structured_output/cheap/fast。

业务只传 required_capabilities + budget；router 将其映射为 ai_engine 场景 tier。
tier 键与 `app/services/ai_engine.py::_get_llm` 的场景键保持一致（general/cost_optimized/
chinese/logic/code/multilingual/high_quality 等），确保复用既有引擎而不重建。
"""

from __future__ import annotations

from typing import List

# ── 总纲 §4.6 能力标签 ───────────────────────────────────────────────
REASONING = "reasoning"
CODING = "coding"
VISION = "vision"
WRITING = "writing"
TRANSLATION = "translation"
STRUCTURED_OUTPUT = "structured_output"
CHEAP = "cheap"
FAST = "fast"

ALL_CAPABILITIES: List[str] = [
    REASONING,
    CODING,
    VISION,
    WRITING,
    TRANSLATION,
    STRUCTURED_OUTPUT,
    CHEAP,
    FAST,
]

# ── 能力标签 → ai_engine 场景 tier 键 ──────────────────────────────
CAPABILITY_TO_TIER: dict[str, str] = {
    REASONING: "logic",          # 逻辑推理模型（DeepSeek/Claude）
    CODING: "code",              # 代码模型
    VISION: "general",           # 暂无视觉模型，回退通用档
    WRITING: "chinese",          # 中文写作模型
    TRANSLATION: "multilingual", # 多语言模型（Gemini）
    STRUCTURED_OUTPUT: "general",
    CHEAP: "cost_optimized",     # 成本优化档（DeepSeek）
    FAST: "general",
}


def normalize(caps) -> List[str]:
    """归一化为合法能力标签列表，过滤未知标签并去重，保持传入顺序。"""
    if not caps:
        return []
    out: List[str] = []
    for c in caps:
        if not isinstance(c, str):
            continue
        c = c.strip().lower()
        if c in ALL_CAPABILITIES and c not in out:
            out.append(c)
    return out
