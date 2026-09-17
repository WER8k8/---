# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""市场洞察技能 — 对标阿里国际 Accio Work 的"生成市场洞察"能力。

背景（2026-09-14 竞品雷达）：Accio Work 是构建在 Qwen 上的 AI 原生应用，对外
第一项能力就是"generate market insights"。我方后端此前全仓零实现（`market_insight`
/ `市场洞察` 检索无命中），DeerFlow 只有内容营销/产品发布/外联三条编排模板。
本模块补的是这条能力链的**技能层**，供 DeerFlow intent、Hermes capability、
以及 `/skills/{name}` 对外端点共用。

诚实纪律（项目"不假交付"铁律）：模型只能基于输入参数与自身知识推理，
因此输出强制携带 `confidence` 与 `verification_required`，禁止把推断写成事实，
禁止编造具体海关数据、真实成交价或不存在的产品认证。
"""

from app.services.foreign_trade.skill_registry import SkillMeta, skill_registry

MARKET_INSIGHT_PROMPT = """你是一位资深外贸出海战略分析师，为建材等工业品卖家做目标市场洞察。

## 洞察对象
- 品类：{category}
- 目标市场：{target_market}
- 我方定位：{our_position}
- 关注周期：{horizon}

## 分析纪律（必须遵守）
1. 只给**可核对的推断**，不要编造具体海关数字、真实成交单价、不存在的认证或法规条款编号。
2. 每个判断都要说明依据来自哪一类公开常识（如"气候带决定外墙保温需求"），而不是假装有数据源。
3. 拿不准的地方明确标 low，并在 verification_required 里列出需要人工核什么。
4. 站在**卖家获客**视角输出：结论要能直接转成内容与投放动作，不要写成行业报告套话。

## 输出格式（严格 JSON，不要任何解释性前后缀）
{{
  "market_size_direction": "市场规模与增长方向的定性判断（150字内）",
  "demand_drivers": [
    {{"driver": "需求驱动因素", "why": "为什么会驱动该品类的采购", "strength": "高/中/低"}}
  ],
  "price_band": {{
    "positioning": "该市场对该品类的价格敏感度定位",
    "band_hint": "定性价格带区间描述（如 低端走量/中端主流/高端认证溢价）",
    "confidence": "高/中/低"
  }},
  "entry_barriers": [
    {{"barrier": "准入壁垒（认证/标准/关税/物流/本地服务）", "how_to_pass": "怎么过", "severity": "高/中/低"}}
  ],
  "buyer_profile": {{
    "typical_roles": ["常见采购决策角色"],
    "priority_criteria": ["买家选型时最在意的点，按优先级"],
    "common_objections": ["最常见的拒绝理由"]
  }},
  "competitor_landscape": {{
    "local_supply": "本地供给成熟度定性描述",
    "import_reliance": "对进口的依赖程度与来源地倾向",
    "differentiation_gap": "我方可以切入但对手没做好的空档"
  }},
  "keyword_and_channel_hints": ["该市场买家会用的检索词/内容方向（可直接进 SEO/GEO）"],
  "action_plan": [
    {{"action": "可执行动作", "owner_role": "负责的角色", "expected_outcome": "预期结果"}}
  ],
  "risks": ["主要不确定性"],
  "confidence": "高/中/低",
  "verification_required": ["需要人工用一手数据核实的条目"],
  "disclaimer": "本洞察为模型基于通用行业常识的推断，未经一手数据核实，不得作为报价或合规承诺依据。"
}}"""

MARKET_INSIGHT_META = SkillMeta(
    name="market_insight",
    display_name="目标市场洞察",
    description="按品类 × 目标市场输出需求驱动、价格带定位、准入壁垒、买家画像与可执行动作（对标 Accio Work 市场洞察）",
    category="research",
    icon="chart",
    prompt_template=MARKET_INSIGHT_PROMPT,
    input_schema={
        "category": {"type": "string", "required": True, "label": "品类"},
        "target_market": {"type": "string", "required": True, "label": "目标市场"},
        "our_position": {
            "type": "string",
            "required": False,
            "label": "我方定位",
            "default": "中等价位、可定制、交期稳定的中国制造商",
        },
        "horizon": {"type": "string", "required": False, "label": "关注周期", "default": "未来 12 个月"},
    },
)

skill_registry.register(MARKET_INSIGHT_META)
