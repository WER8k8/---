SYSTEM_PROMPTS = {
    "seo_optimizer": """你是一个专业的SEO内容优化专家，专注于建材行业网站优化。
请遵循以下原则：
1. 保持技术参数的绝对准确，不可修改密度、强度等级、导热系数等
2. 自然融入关键词，避免关键词堆砌
3. 遵守广告法，不使用"最"、"第一"、"顶级"等禁用词
4. 保持专业、权威的行业语言风格
5. 针对百度搜索引擎优化""",

    "content_writer": """你是一个建材行业专业内容写手。
写作要求：
1. 以轻集料混凝土为核心主题
2. 引用JGJ/T 12-2019、GB/T 17431-2010等行业标准
3. 内容结构清晰，包含H2/H3层次
4. 每篇800-2000字
5. 自然包含长尾关键词""",

    "meta_optimizer": """你是一个SEO Meta标签优化专家。
规则：
1. Meta标题：15-30字，包含核心关键词在前
2. Meta描述：50-120字，含关键词+行动号召
3. 每个页面唯一，不重复
4. 符合百度Meta标签规范""",

    "schema_generator": """你是一个结构化数据(Schema Markup)生成专家。
为建材行业网站生成JSON-LD格式的结构化数据。
支持类型：Product、FAQPage、BreadcrumbList、Organization、
Article、LocalBusiness、Review""",

    "keyword_analyzer": """你是一个关键词分析专家。
分析维度：
1. 搜索意图：信息型/导航型/交易型
2. 竞争难度：低/中/高
3. 相关长尾关键词建议
4. 用户搜索场景分析
专注建材、混凝土、工程材料行业关键词""",
}


PRODUCT_SEO_TEMPLATE = """产品名称：{product_name}
产品类别：{category}
核心参数：{parameters}
应用场景：{scenarios}

SEO要求：
- Meta标题：包含{product_name}和{category}
- Meta描述：突出{key_advantages}优势
- 关键词：{keywords}
- 技术参数准确性：须与官方数据一致"""


CONTENT_SEO_TEMPLATE = """文章标题：{title}
文章摘要：{summary}
目标关键词：{keywords}（需自然出现2-3次）
文章长度：{word_count}字

要求：
1. 首段100字内出现目标关键词
2. H2标题包含长尾关键词
3. 结尾引导CTA
4. 引用行业标准增强EEAT"""


LLMS_TXT_TEMPLATE = """# LLMs.txt

## 品牌信息

{company_name} - {company_tagline}

## 核心产品

{product_list}

## AI指令

{ai_instructions}

## 技术标准参考

{technical_standards}

## 联系方式

{contact_info}"""


EEAT_SIGNAL_TEMPLATES = {
    "experience": "展示{company_name}在{field}行业{year}年的实践经验，累计服务{client_count}个项目",
    "expertise": "引用行业标准{standard}，技术团队持有{qualifications}等专业资质",
    "authoritativeness": "获得{certifications}等行业认证，参与{industry_events}等专业活动",
    "trustworthiness": "提供完整的{support_info}，{guarantee}质保承诺",
}


def build_keyword_strategy_prompt(keyword: str, keyword_type: str = "short_tail") -> str:
    prompt_map = {
        "short_tail": f"为短尾关键词'{keyword}'制定内容策略：分析搜索意图、推荐5个长尾变体、建议页面类型和内容角度",
        "long_tail": f"为长尾关键词'{keyword}'制定内容策略：推荐自然融入位置、相关语义场词汇、用户搜索场景",
        "product": f"为产品关键词'{keyword}'制定内容策略：推荐技术参数展示方式、应用场景案例、对比优化建议",
    }
    return prompt_map.get(keyword_type, prompt_map["short_tail"])


def get_optimization_prompt(content_type: str, content: str, keywords: list[str], technical_params: dict = None) -> str:
    base = SYSTEM_PROMPTS.get("seo_optimizer", "")
    keywords_str = ", ".join(keywords)
    params_str = str(technical_params) if technical_params else "无"

    return f"""{base}

内容类型: {content_type}
目标关键词: {keywords_str}
技术参数(不可修改): {params_str}

原始内容:
{content}

请进行SEO优化。"""
