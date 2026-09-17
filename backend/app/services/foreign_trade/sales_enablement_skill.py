# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""销售赋能技能 — 对应 sales-enablement SKILL.md。"""

from app.services.foreign_trade.skill_registry import SkillMeta, skill_registry

SALES_ENABLEMENT_PROMPT = """你是一位资深 B2B 销售赋能专家，擅长制作销售资料和话术。

## 任务
根据以下信息生成销售赋能资料。

## 产品信息
{product_info}

## 目标市场
{target_market}

## 资料类型
{asset_type}

## 资料类型说明
- pitch_deck：10 页销售演示文稿大纲
- one_pager：单页产品介绍（结构化要点）
- objection_handling：常见异议处理话术（至少 8 个）
- demo_script：产品演示脚本（开场→痛点→方案→证明→收尾）
- battle_card：竞品对比卡片（我方优势 vs 竞品弱点）
- roi_calculator：投资回报计算模板

## 输出格式（JSON）
{{
  "asset_type": "{asset_type}",
  "title": "资料标题",
  "content": {{
    "sections": [
      {{"heading": "标题", "content": "内容（支持要点列表）"}}
    ]
  }},
  "key_talking_points": ["话术要点1", "话术要点2", "话术要点3"],
  "target_persona": "目标受众",
  "usage_guidance": "使用场景说明"
}}"""

SALES_ENABLEMENT_META = SkillMeta(
    name="sales_enablement",
    display_name="销售赋能",
    description="生成销售演示、话术、异议处理、ROI 计算等销售资料",
    category="enablement",
    icon="presentation",
    prompt_template=SALES_ENABLEMENT_PROMPT,
    input_schema={
        "product_info": {"type": "string", "required": True, "label": "产品信息"},
        "target_market": {"type": "string", "required": True, "label": "目标市场"},
        "asset_type": {"type": "string", "required": True, "label": "资料类型"},
    },
)

skill_registry.register(SALES_ENABLEMENT_META)
