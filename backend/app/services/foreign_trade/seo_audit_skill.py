"""SEO 审计技能 — 对应 seo-audit SKILL.md。"""

from app.services.foreign_trade.skill_registry import SkillMeta, skill_registry

SEO_AUDIT_PROMPT = """你是一位资深 SEO 专家，擅长外贸网站 SEO 审计和优化建议。

## 审计目标
{target_url}

## 网站类型
{site_type}

## 审计维度
1. **技术 SEO**：页面速度、移动端适配、结构化数据、robots.txt、sitemap.xml
2. **页面 SEO**：title/meta description/H1 标签/图片 alt/URL 结构
3. **内容质量**：关键词密度、内容深度、多语言支持、E-E-A-T 信号
4. **外链分析**：外链数量、质量、锚文本分布
5. **用户体验**：导航结构、CTA 布局、信任信号、询盘表单

## 输出格式（JSON）
{{
  "overall_score": 75,
  "technical_seo": {{
    "score": 80,
    "issues": ["问题1", "问题2"],
    "recommendations": ["建议1", "建议2"]
  }},
  "on_page_seo": {{
    "score": 70,
    "issues": ["问题1"],
    "recommendations": ["建议1"]
  }},
  "content_quality": {{
    "score": 65,
    "issues": ["问题1"],
    "recommendations": ["建议1"]
  }},
  "priority_fixes": [
    {{"issue": "问题描述", "impact": "高/中/低", "effort": "高/中/低", "fix": "修复方案"}}
  ],
  "quick_wins": ["可快速改善的项1", "可快速改善的项2"]
}}"""

SEO_AUDIT_META = SkillMeta(
    name="seo_audit",
    display_name="SEO 审计",
    description="对网站进行全面 SEO 审计，输出技术问题、优化建议和优先级排序",
    category="seo",
    icon="globe",
    prompt_template=SEO_AUDIT_PROMPT,
    input_schema={
        "target_url": {"type": "string", "required": True, "label": "目标网址"},
        "site_type": {"type": "string", "required": False, "label": "网站类型", "default": "B2B 外贸官网"},
    },
)

skill_registry.register(SEO_AUDIT_META)
