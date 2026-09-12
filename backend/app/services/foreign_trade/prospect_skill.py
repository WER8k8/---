"""智能搜客技能 — 对应 prospecting SKILL.md。"""

from app.services.foreign_trade.skill_registry import SkillMeta, skill_registry

PROSPECT_PROMPT = """你是一位资深 B2B 外贸获客专家，擅长全球市场客户开发。

## 任务
根据以下条件搜索潜在客户，生成结构化的候选客户列表。

## 搜索条件
- 产品/行业：{product_keywords}
- 目标市场：{countries}
- 客户类型：{customer_type}
- 排除词：{exclude_words}

## 要求
1. 使用 Google、LinkedIn、行业目录等公开数据源
2. 每个候选客户必须包含：公司名、国家、行业、官网、联系人、邮箱、匹配评分
3. 匹配评分（0-100）：基于产品相关性 40% + 市场匹配 30% + 联系人完整度 30%
4. 提供证据链（来源 URL、匹配依据）
5. 优先找经销商、系统集成商、OEM、EPC 工程商
6. 排除招聘网站、二手交易、新闻媒体等非目标结果

## 输出格式（JSON 数组）
[{{"company_name": "...", "country": "...", "industry": "...", "website": "...", "contact_name": "...", "contact_title": "...", "email": "...", "phone": "...", "score": 85, "evidence": ["来源URL1", "来源URL2"], "notes": "匹配原因简述"}}]

请输出 {top_n} 个高价值候选客户。"""

PROSPECT_META = SkillMeta(
    name="prospect",
    display_name="智能搜客",
    description="根据产品关键词和目标市场，自动搜索全球潜在客户并评分排序",
    category="prospect",
    icon="search",
    prompt_template=PROSPECT_PROMPT,
    input_schema={
        "product_keywords": {"type": "string", "required": True, "label": "产品关键词"},
        "countries": {"type": "string", "required": True, "label": "目标市场"},
        "customer_type": {"type": "string", "required": False, "label": "客户类型", "default": "经销商/分销商"},
        "exclude_words": {"type": "string", "required": False, "label": "排除词", "default": "job, used, repair, school, news"},
        "top_n": {"type": "integer", "required": False, "label": "返回数量", "default": 10},
    },
)

skill_registry.register(PROSPECT_META)
