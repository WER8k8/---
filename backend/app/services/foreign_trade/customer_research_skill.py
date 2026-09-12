"""客户调研技能 — 对应 customer-research SKILL.md。"""

from app.services.foreign_trade.skill_registry import SkillMeta, skill_registry

CUSTOMER_RESEARCH_PROMPT = """你是一位资深 B2B 客户调研专家，擅长从公开信息中提取客户洞察。

## 调研目标
对以下客户进行深度调研，提取关键商业情报。

## 客户信息
- 公司名：{company_name}
- 官网：{website}
- 国家：{country}
- 行业：{industry}

## 调研维度
1. **公司概况**：规模、历史、主营业务、核心产品
2. **采购模式**：采购频率、供应商偏好、决策流程
3. **痛点分析**：行业常见痛点 + 该客户特有挑战
4. **决策链**：关键决策人、采购部门结构
5. **竞争格局**：现有供应商、替代方案
6. **切入策略**：最佳接触时机、话术切入点、差异化卖点

## 输出格式（JSON）
{{
  "company_overview": "公司概况（100字内）",
  "procurement_pattern": "采购模式分析",
  "pain_points": ["痛点1", "痛点2", "痛点3"],
  "decision_makers": [{{"name": "...", "title": "...", "influence": "高/中/低"}}],
  "existing_suppliers": ["供应商1", "供应商2"],
  "entry_strategy": {{
    "best_timing": "最佳接触时机",
    "approach": "切入话术",
    "differentiator": "差异化卖点"
  }},
  "confidence": "高/中/低",
  "sources": ["数据来源URL"]
}}"""

CUSTOMER_RESEARCH_META = SkillMeta(
    name="customer_research",
    display_name="客户深度调研",
    description="从公开信息中提取客户画像、采购模式、决策链和切入策略",
    category="research",
    icon="search",
    prompt_template=CUSTOMER_RESEARCH_PROMPT,
    input_schema={
        "company_name": {"type": "string", "required": True, "label": "客户公司名"},
        "website": {"type": "string", "required": False, "label": "官网", "default": ""},
        "country": {"type": "string", "required": True, "label": "国家"},
        "industry": {"type": "string", "required": True, "label": "行业"},
    },
)

skill_registry.register(CUSTOMER_RESEARCH_META)
