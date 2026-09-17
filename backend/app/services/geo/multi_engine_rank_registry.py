# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""多流量入口排名注册表 — 百度 / 豆包 / 360 / 大模型 / 出海搜索 分轨探测。

各入口 ranking 机制不同，不可共用一套 SEO 规则；本模块定义探针映射与蒸馏风险等级。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

EngineFamily = Literal["classic_search", "ai_search", "ai_browser", "llm_chat"]
ProbeVia = Literal["geo_engine", "seo_matrix", "headless_exploration", "webmaster", "ai_search_api"]
DistillationRisk = Literal["high", "medium", "low"]
Market = Literal["domestic", "global", "both"]

# geo_model_id 对应 geo_engine_service.GEOEngine.MODELS[].id
# 第 8 列 market: domestic=国内 classic/AI, global=出海, both=双市场
_TRAFFIC_ENGINES: tuple[tuple[str, str, EngineFamily, str | None, str, DistillationRisk, str, Market], ...] = (
    # ── 国内传统搜索 ──
    ("baidu", "百度搜索", "classic_search", None, "seo_matrix", "medium", "凤巢+百度系 SERP，与 GEO 分轨", "domestic"),
    ("sogou", "搜狗搜索", "classic_search", None, "headless_exploration", "medium", "腾讯系 SERP，长尾词覆盖", "domestic"),
    ("shenma", "神马搜索", "classic_search", None, "headless_exploration", "medium", "UC/阿里系移动搜索", "domestic"),
    ("so360", "360 好搜", "classic_search", None, "headless_exploration", "medium", "360 经典网页搜索（与纳米 AI 分轨）", "domestic"),
    # ── 出海传统搜索 ──
    ("google", "Google 搜索", "classic_search", None, "webmaster", "medium", "GSC 收录 + SERP 排名", "global"),
    ("bing", "Bing 搜索", "classic_search", None, "webmaster", "medium", "Bing Webmaster + 英文 SERP", "global"),
    # ── 国内 AI 浏览器 / 搜索 ──
    ("doubao", "豆包", "ai_browser", "doubao", "geo_engine", "high", "字节系 AI 浏览器/助手，蒸馏频繁", "domestic"),
    ("yuanbao", "腾讯元宝", "ai_browser", None, "headless_exploration", "high", "微信生态权重，待 headless 探针", "domestic"),
    ("qwen", "通义千问", "ai_search", "qwen", "geo_engine", "high", "阿里系 AI 搜索与商户场景", "domestic"),
    ("wenxin", "文心一言", "ai_search", None, "headless_exploration", "high", "百度大模型，待 API/探针", "domestic"),
    ("360", "360 纳米 AI", "ai_search", None, "headless_exploration", "high", "360 系 AI 搜索，机制独立", "domestic"),
    ("kimi", "Kimi", "llm_chat", None, "headless_exploration", "medium", "长文引用场景", "domestic"),
    # ── 双市场 / 出海 LLM ──
    ("deepseek", "DeepSeek", "llm_chat", "deepseek", "geo_engine", "high", "独立 AI 搜索入口", "both"),
    ("chatgpt", "ChatGPT", "llm_chat", "openai", "geo_engine", "medium", "出口询盘与英文 probe", "global"),
    ("gemini", "Gemini", "llm_chat", "gemini", "geo_engine", "medium", "全球 AI 搜索对照", "global"),
    ("claude", "Claude", "llm_chat", "anthropic", "geo_engine", "medium", "Anthropic 对话与 AEO 抽检", "global"),
    ("nvidia", "NVIDIA NIM", "llm_chat", "nvidia", "geo_engine", "low", "NIM 托管模型对照探针", "global"),
    ("perplexity", "Perplexity", "ai_search", None, "ai_search_api", "medium", "PERPLEXITY_API_KEY → ai_search_probe_service", "global"),
    ("copilot", "Microsoft Copilot", "ai_search", None, "ai_search_api", "medium", "Bing/Copilot 无公开榜；诚实 not_configured", "global"),
    ("google_aio", "Google AI 概览", "ai_search", None, "headless_exploration", "high", "SGE / AI Overviews 推荐位", "global"),
)

# InclusionStatus.search_engine 与注册表 id 可能不一致（历史字段别名）
_ENGINE_STAT_ALIASES: dict[str, frozenset[str]] = {
    "chatgpt": frozenset({"chatgpt", "openai"}),
    "so360": frozenset({"so360", "360so", "360_search"}),
}


@dataclass(frozen=True)
class TrafficEngine:
    id: str
    display_name: str
    family: EngineFamily
    geo_model_id: str | None
    probe_via: ProbeVia
    distillation_risk: DistillationRisk
    notes: str
    market: Market = "both"
    @property
    def probe_ready(self) -> bool:
        """probe_ready。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self.probe_via == "geo_engine" and bool(self.geo_model_id):
            return True
        if self.probe_via == "ai_search_api" and self.id == "perplexity":
            import os
            return len((os.getenv("PERPLEXITY_API_KEY") or os.getenv("AI_PERPLEXITY_API_KEY") or "").strip()) >= 8
        return False

    @property
    def probe_status_label(self) -> str:
        """probe_status_label。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self.probe_ready:
            return "API 探针"
        if self.probe_via == "seo_matrix":
            return "收录探针"
        if self.probe_via == "webmaster":
            return "站长工具"
        if self.probe_via == "ai_search_api":
            return "AI Search API"
        if self.probe_via == "headless_exploration":
            return "探索中"
        return "待接入"


def engine_stat_keys(engine_id: str) -> frozenset[str]:
    """实现 enginestat键 的功能。
    
    :param engine_id: 参数 engine_id（类型: str）
    :return: 返回 frozenset[str] 结果
    """
    return _ENGINE_STAT_ALIASES.get(engine_id, frozenset({engine_id}))


def all_traffic_engines() -> list[TrafficEngine]:
    """实现 alltrafficengines 的功能。
    
    :return: 返回 list[TrafficEngine] 结果
    """
    return [
        TrafficEngine(
            id=eid,
            display_name=name,
            family=family,
            geo_model_id=mid,
            probe_via=via,
            distillation_risk=risk,
            notes=notes,
            market=market,
        )
        for eid, name, family, mid, via, risk, notes, market in _TRAFFIC_ENGINES
    ]


def probe_ready_engines() -> list[TrafficEngine]:
    """实现 探测readyengines 的功能。
    
    :return: 返回 list[TrafficEngine] 结果
    """
    return [e for e in all_traffic_engines() if e.probe_ready]


def exploration_engines() -> list[TrafficEngine]:
    """实现 explorationengines 的功能。
    
    :return: 返回 list[TrafficEngine] 结果
    """
    return [e for e in all_traffic_engines() if not e.probe_ready]


def engines_by_distillation_risk(min_risk: DistillationRisk = "high") -> list[TrafficEngine]:
    """实现 enginesbydistillationrisk 的功能。
    
    :param min_risk: 参数 min_risk（类型: DistillationRisk）
    :return: 返回 list[TrafficEngine] 结果
    """
    order = {"high": 3, "medium": 2, "low": 1}
    threshold = order.get(min_risk, 2)
    return [e for e in all_traffic_engines() if order.get(e.distillation_risk, 0) >= threshold]


def default_probe_keywords() -> list[dict[str, str]]:
    """每日 Hermes 探针用默认品类（可通过 env 扩展）。"""
    import os
    raw = (os.getenv("HERMES_RANK_PROBE_KEYWORDS") or "").strip()
    if raw:
        items = []
        for part in raw.split("|"):
            bits = part.split(",")
            if len(bits) >= 2:
                items.append(
                    {
                        "brand": bits[0].strip(),
                        "product_category": bits[1].strip(),
                        "region": bits[2].strip() if len(bits) > 2 else "国内工地/出口",
                    }
                )
        if items:
            return items
    return [
        {
            "brand": "优丁建材",
            "product_category": "聚氨酯轻集料混凝土",
            "region": "天津工地集采",
        },
        {
            "brand": "岩棉保温板",
            "product_category": "A1级防火岩棉板出口",
            "region": "中东工程项目",
        },
    ]
