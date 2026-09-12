"""竞品画像技能 — 对应 competitor-profiling SKILL.md。"""

from app.services.foreign_trade.skill_registry import SkillMeta, skill_registry

COMPETITOR_PROFILE_PROMPT = """你是一位资深竞争情报分析师，擅长从公开信息中构建竞品画像。

## 竞品信息
- 公司名：{competitor_name}
- 官网：{website}
- 所在行业：{industry}

## 我方产品优势
{our_advantages}

## 画像维度
1. **公司概况**：规模、成立时间、主营产品、核心市场
2. **产品线**：主要产品、价格区间、技术特点
3. **市场策略**：目标客户、销售渠道、定价策略
4. **优势分析**：核心竞争力、市场口碑
5. **弱点分析**：产品缺陷、服务短板、价格劣势
6. **应对策略**：我们如何差异化竞争

## 输出格式（JSON）
{{
  "company_overview": "公司概况",
  "products": [{{"name": "...", "price_range": "...", "features": "..."}}],
  "market_strategy": "市场策略分析",
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["弱点1", "弱点2"],
  "threat_level": "高/中/低",
  "battle_card": {{
    "our_advantage": "我们的优势",
    "their_weakness": "他们的弱点",
    "talk_track": "谈判话术",
    "price_strategy": "报价策略"
  }},
  "sources": ["数据来源URL"]
}}"""

COMPETITOR_PROFILE_META = SkillMeta(
    name="competitor_profile",
    display_name="竞品画像",
    description="从官网和公开信息构建竞品画像，生成应对策略和打法卡",
    category="competitor",
    icon="target",
    prompt_template=COMPETITOR_PROFILE_PROMPT,
    input_schema={
        "competitor_name": {"type": "string", "required": True, "label": "竞品公司名"},
        "website": {"type": "string", "required": True, "label": "竞品官网"},
        "industry": {"type": "string", "required": True, "label": "所在行业"},
        "our_advantages": {"type": "string", "required": True, "label": "我方产品优势"},
    },
)

skill_registry.register(COMPETITOR_PROFILE_META)
