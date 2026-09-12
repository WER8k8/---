"""营销文案技能 — 对应 copywriting SKILL.md。"""

from app.services.foreign_trade.skill_registry import SkillMeta, skill_registry

COPYWRITING_PROMPT = """你是一位资深外贸营销文案专家，擅长撰写面向海外买家的营销内容。

## 任务
根据以下信息生成营销文案。

## 产品信息
{product_info}

## 目标受众
{target_audience}

## 文案类型
{copy_type}

## 文案类型说明
- product_description：产品详情页文案（特性→优势→利益→证明）
- ad_copy：Google/Facebook 广告文案（标题+描述+CTA）
- social_post：LinkedIn/Facebook 社媒帖子
- landing_page：落地页文案（Hero→痛点→方案→证明→CTA）
- email_sequence：邮件序列（3 封：开场→价值→收尾）
- case_study：客户案例故事（背景→挑战→方案→结果）

## 输出格式（JSON）
{{
  "copy_type": "{copy_type}",
  "headline": "主标题",
  "subheadline": "副标题",
  "body": "正文内容",
  "cta": "行动号召",
  "variations": [
    {{"label": "版本A", "headline": "...", "body": "..."}},
    {{"label": "版本B", "headline": "...", "body": "..."}}
  ],
  "seo_keywords": ["关键词1", "关键词2"],
  "target_emotion": "目标情感（信任/紧迫/好奇）"
}}"""

COPYWRITING_META = SkillMeta(
    name="copywriting",
    display_name="营销文案",
    description="生成产品描述、广告文案、社媒内容、落地页、邮件序列等外贸营销文案",
    category="content",
    icon="edit",
    prompt_template=COPYWRITING_PROMPT,
    input_schema={
        "product_info": {"type": "string", "required": True, "label": "产品信息"},
        "target_audience": {"type": "string", "required": True, "label": "目标受众"},
        "copy_type": {"type": "string", "required": True, "label": "文案类型"},
    },
)

skill_registry.register(COPYWRITING_META)
