# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""供应商/同行比较排序卡 — 对标阿里国际 Accio Work 的"比价与供应商比较"能力链。

背景（TODO.md §11）：Accio Work 的多 agent 分工里有"找供应商 + 比价"，我方此前
只有 `competitor_profile`（单家竞品画像），缺**多家横向排序**这一环。

卖家视角的正确用法（不是照抄买家视角）：
  · 对外：买家侧采购 agent 提问"这几家怎么选"时，我方要有结构化对比资产可被引用；
  · 对内：直接产出打单用的排序卡与差异化话术，接进 BOQ 核价与谈单话术。

诚实纪律：不得编造真实公司名、真实价格、真实认证编号。候选主体由调用方
（人工或 `matching_engine` 结果）传入；模型只负责按维度做**定性**比较与排序理由。
"""

from app.services.foreign_trade.skill_registry import SkillMeta, skill_registry

SUPPLIER_COMPARE_PROMPT = """你是一位资深外贸采购与竞争分析专家，负责把给定的若干供给方做成横向对比排序卡。

## 比较对象
- 品类：{category}
- 目标市场：{target_market}
- 采购/竞争关注点：{criteria}
- 待比较主体（由调用方提供，禁止新增或杜撰主体）：
{candidates}
- 我方情况：{our_position}

## 比较纪律（必须遵守）
1. 只能对上面列出的主体做比较，**不得引入任何未列出的公司或品牌**。
2. 主体信息里没给的字段一律写"未披露"，严禁猜测具体价格、MOQ 数字、认证编号。
3. 排序必须给**可复述的理由**，理由只能引用输入字段或通用行业常识。
4. 明确区分"事实（来自输入）"与"推断（来自常识）"，推断项进 inference 字段。

## 输出格式（严格 JSON，不要任何解释性前后缀）
{{
  "category": "{category}",
  "target_market": "{target_market}",
  "dimensions": ["本次实际参与比较的维度"],
  "ranking": [
    {{
      "rank": 1,
      "subject": "主体名（必须来自输入）",
      "score_hint": "强/中/弱",
      "wins": ["该主体领先的点"],
      "gaps": ["该主体明显的短板"],
      "reason": "为什么排在这个位置",
      "facts_used": ["引用自输入的字段事实"],
      "inference": ["基于行业常识的推断，非事实"]
    }}
  ],
  "verdict": {{
    "best_overall": "综合最优选（主体名）",
    "best_for_price": "价格敏感场景最优选",
    "best_for_compliance": "认证/标准门槛场景最优选",
    "avoid_when": "什么情况下不该选谁"
  }},
  "our_play": {{
    "differentiator": "我方差异化卖点（一句话）",
    "talk_track": "面对这些对手时的话术要点",
    "price_strategy": "报价策略建议（定性，不给具体数字）",
    "proof_needed": "要赢单还需补哪些证据（检测报告/案例/交期数据）"
  }},
  "confidence": "高/中/低",
  "verification_required": ["需要用一手资料核实的条目"],
  "disclaimer": "本对比为模型基于输入信息与行业常识的定性推断，未核实真实报价与认证状态，不得直接对外承诺。"
}}"""

SUPPLIER_COMPARE_META = SkillMeta(
    name="supplier_compare",
    display_name="供应商比较排序卡",
    description="对给定品类与目标市场下的多家供给方做横向维度比较与排序，输出领先点、短板、打单话术（对标 Accio Work 比价/供应商比较）",
    category="competitor",
    icon="compare",
    prompt_template=SUPPLIER_COMPARE_PROMPT,
    input_schema={
        "category": {"type": "string", "required": True, "label": "品类"},
        "target_market": {"type": "string", "required": True, "label": "目标市场"},
        "candidates": {
            "type": "string",
            "required": True,
            "label": "待比较主体（多行文本，每行一家）",
            "default": "",
        },
        "criteria": {
            "type": "string",
            "required": False,
            "label": "采购/竞争关注点",
            "default": "价格、认证合规、交期、MOQ、售后与本地支持",
        },
        "our_position": {
            "type": "string",
            "required": False,
            "label": "我方情况",
            "default": "中等价位、可定制、交期稳定的中国制造商",
        },
    },
)

skill_registry.register(SUPPLIER_COMPARE_META)
