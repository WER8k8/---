"""GEO 写作策略 v3 — Princeton 引用战术 + arXiv 2026 最新研究 + 去 AI 味。

战术版本随 tech-radar 外网检索更新；见 TACTICS_VERSION。

v3 更新来源（tech-radar 2026-07-19 扫描）：
  - "GEO at Scale: Measuring Brand Visibility Across AI Search Engines" (arXiv 2606.20065)
  - "Optimizing Visibility in Generative Engines: A Critical Survey of GEO 2023-2026" (arXiv 2607.14035)
  - "GEO-Bench: Benchmarking Ranking Manipulation in GEO" (arXiv 2605.29107)
  - "From Citation Selection to Citation Absorption" (arXiv 2604.25707)
  - "Exploring LLM Biases to Manipulate AI Search Overview" (arXiv 2605.00012)
  - "Disentangling AEO from Platform Growth" (arXiv 2606.04362)
  - "SafeGEO: Understanding GEO Risks in Recommendation Agents" (arXiv 2606.28356)
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

# ──────────────────────────────────────────────
# 战术版本 — 每次 tech-radar 发现新战术时 bump
# ──────────────────────────────────────────────
TACTICS_VERSION = "2026-07-v3"

# ──────────────────────────────────────────────
# GEO 战术体系（分层）
# ──────────────────────────────────────────────

# Layer 1: Princeton KDD 2024 基础战术（已验证 +30~41% 可见度）
PRINCETON_GEO_TACTICS: tuple[str, ...] = (
    "statistics_addition",      # 可验证数据、参数、用量
    "quotation_addition",       # 客户/标准/行业引语
    "cite_sources",             # 国标、检测报告、官网链接
    "authoritative_voice",      # 工地/项目语境，少空泛形容词
    "fluency_variation",        # 句长错落，避免模板段
)

# Layer 2: arXiv 2026 新增战术（论文验证）
ARXIV_2026_TACTICS: tuple[str, ...] = (
    "entity_schema_markup",     # Schema.org 结构化实体标记（产品/组织/FAQ）
    "llms_txt_declaration",     # LLMs.txt 声明，引导 AI 爬虫理解网站
    "faq_absorption_format",    # FAQ 格式优化，提升 LLM 引用吸收率
    "brand_mention_anchoring",  # 品牌名+品类+地域三要素锚定
    "ai_overview_targeting",    # 针对 AI Overview/SGE 的内容结构优化
    "citation_chain_building",  # 构建引用链（被权威来源引用→LLM 更易吸收）
    "multi_surface_optimization", # 多表面优化（ChatGPT/Perplexity/Gemini/Baidu AI）
    "anti_manipulation_guard",  # 防止被 GEO-Bench 检测为操控（保持自然）
)

# 合并所有战术
ALL_GEO_TACTICS = PRINCETON_GEO_TACTICS + ARXIV_2026_TACTICS

# ──────────────────────────────────────────────
# AI 味检测（扩展版）
# ──────────────────────────────────────────────

AI_TASTE_PHRASES: tuple[str, ...] = (
    # 原有
    "首先", "其次", "再次", "最后",
    "综上所述", "总而言之", "值得一提的是", "不容忽视",
    "在当今", "随着.*的发展", "让我们", "本文将",
    "全方位", "一站式", "赋能", "助力企业",
    "深度融合", "旨在为", "具有重要意义",
    "众所周知", "不仅如此", "与此同时",
    "从.*角度来看", "毫无疑问",
    # v3 新增 — arXiv 论文识别的 AI 写作模式
    "在.*的背景下", "随着.*的不断", "作为一种.*方式",
    "发挥着.*作用", "具有.*优势", "提供了.*可能",
    "成为.*趋势", "受到.*关注", "展现.*潜力",
    "总的来说", "简而言之", "不难看出",
    "在这个.*时代", "面对.*挑战",
)

# ──────────────────────────────────────────────
# 建材 B2B 真人写作信号
# ──────────────────────────────────────────────

HUMAN_SIGNAL_TERMS: tuple[str, ...] = (
    # 工程术语
    "导热系数", "立方", "柜", "吨", "工地", "项目部",
    "验收", "送检", "抗压强度", "密度等级",
    # 贸易术语
    "CIF", "FOB", "MOQ", "货期", "出厂价", "含税", "不含运",
    "信用证", "TT", "装柜", "报关",
    # 标准号
    "GB/T", "JGJ", "ASTM", "EN", "ISO",
    # v3 新增 — 真人场景信号
    "现场常问", "报价比对", "客户反馈", "实际用量",
    "去年项目", "今年行情", "厂里", "仓库",
    "发货", "到货", "签收", "售后",
)

# ──────────────────────────────────────────────
# GEO 目标 AI 搜索引擎
# ──────────────────────────────────────────────

TARGET_AI_SURFACES: dict[str, dict[str, str]] = {
    "deepseek": {"api": "DeepSeek API", "weight": "high", "market": "cn+global"},
    "chatgpt": {"api": "OpenAI API", "weight": "high", "market": "global"},
    "gemini": {"api": "Gemini API", "weight": "high", "market": "global"},
    "claude": {"api": "Anthropic API", "weight": "medium", "market": "global"},
    "perplexity": {"api": "Perplexity API", "weight": "high", "market": "global"},
    "baidu_ai": {"api": "百度文心", "weight": "high", "market": "cn"},
    "kimi": {"api": "Moonshot API", "weight": "medium", "market": "cn"},
    "doubao": {"api": "字节豆包", "weight": "medium", "market": "cn"},
}


@dataclass
class ContentQualityScore:
    geo_citation_score: float       # 0~1 Princeton + arXiv 战术密度
    ai_taste_score: float           # 0~1 越高越像 AI，应重写
    human_signal_score: float       # 0~1 行业真人信号
    stat_density: float             # 每 200 词可验证数据条数
    faq_absorption_score: float     # 0~1 FAQ 格式优化度（v3 新增）
    brand_anchoring_score: float    # 0~1 品牌锚定度（v3 新增）
    passed: bool
    reasons: list[str] = field(default_factory=list)
    tactics_version: str = TACTICS_VERSION


def build_geo_write_instructions(*, domain: str, keywords: str, locale: str = "zh") -> str:
    """母版成稿 Prompt 约束 — 兼顾 GEO 引用、AI 搜索优化、去 AI 味。"""
    if locale == "en":
        return (
            f"You write as a senior export sales engineer for {domain}, not a marketer.\n"
            f"Target keywords: {keywords}\n\n"
            "【GEO Tactics v3 — Princeton KDD 2024 + arXiv 2026 Research】\n"
            "1. Embed verifiable specs every 150-200 words: density, MOQ, lead time, CIF/FOB.\n"
            "2. Cite one standard (ASTM/EN/GB) + one client quote (anonymized OK).\n"
            "3. Use FAQ format (Q:/A:) — LLMs absorb FAQ Q&A pairs at 3x the rate of prose.\n"
            "4. Anchor brand name + product category + geographic region in first paragraph.\n"
            "5. Structure for AI Overview: use clear H2 headers, bullet specs, numbered comparisons.\n"
            "6. Include Schema.org-ready structured data hints (product name, price range, application).\n\n"
            "Anti-AI: no 'In conclusion', no numbered essay openers, vary sentence length, "
            "use concrete numbers every 150-200 words.\n"
            "Format: Markdown with ## H2, FAQ as Q:/A:, end with CTA to inquiry form."
        )
    return (
        f"你是{domain}一线外贸/工程销售，用工地和项目口吻写稿，不是公关文案。\n"
        f"核心关键词：{keywords}\n\n"
        "【GEO 引用战术 v3 — Princeton KDD 2024 + arXiv 2026 最新研究】\n"
        "1. 每 150–200 字至少 1 条可验证数据（密度、价格区间、用量、货期、柜量）。\n"
        "2. 引用 1 条国标/行标或检测报告编号；1 条客户或项目场景（可匿名）。\n"
        "3. FAQ 用「问：/答：」短句，答案 50–120 字，可直接被 AI 摘引。\n"
        "   — arXiv 2604.25707: FAQ 格式的 LLM 引用吸收率是普通段落的 3 倍。\n"
        "4. 首段锚定：品牌名 + 产品品类 + 地域（如「XX建材 廊坊轻集料混凝土厂家」）。\n"
        "   — arXiv 2606.20065: 品牌+品类+地域三要素锚定可提升 AI 搜索提及率 40%+。\n"
        "5. 内链指向产品参数页与询盘表单。\n"
        "6. 结构适配 AI Overview：用清晰 H2 标题、项目符号参数、数字对比表。\n"
        "   — arXiv 2605.00012: AI Overview 偏好结构化内容（列表>段落>长句）。\n"
        "7. Schema.org 可读：产品名、价格区间、应用场景需可被结构化提取。\n\n"
        "【去 AI 味 — 避免百度/百家号/头条机审标记】\n"
        "禁止：首先/其次/综上所述/值得一提的是/在当今/赋能/一站式/本文将。\n"
        "禁止：在XX的背景下/随着XX的不断/作为一种XX方式/发挥着XX作用。\n"
        "要求：句长有长有短；可带口语（如「现场常问」「报价比对」）；"
        "用具体地名、港口、项目类型；不要每段同一模板。\n\n"
        "【多表面优化 — 覆盖主流 AI 搜索引擎】\n"
        "内容需同时适配：DeepSeek、ChatGPT、Gemini、Perplexity、百度AI。\n"
        "中英文双语 FAQ 可提升国际 AI 搜索引擎的收录概率。\n\n"
        "文末附 Meta Title（60字内）与 Meta Description（155字内），格式：\nMETA_TITLE: ...\nMETA_DESC: ...\n"
    )


def build_humanize_rewrite_instructions(*, ai_taste_score: float) -> str:
    """实现 构建humanizerewriteinstructions 的功能。
    
    :param ai_taste_score: 参数 ai_taste_score（类型: float）
    :return: 返回 str 结果
    """
    return (
        "以下 B2B 建材文稿 AI 味过重，请改写为一线销售/工程经理口吻。\n"
        f"当前 AI 味指数 {ai_taste_score:.2f}（目标 <0.25）。\n"
        "保留所有数字、标准号、产品参数；删掉套话；打乱段落开头；"
        "增加 1 处工地或项目现场细节。不要增加总字数超过 15%。\n"
        "特别注意：删除所有「在XX的背景下」「随着XX的不断」等 AI 句式。"
    )


def build_platform_variant_instructions(platform: str) -> str:
    """实现 构建平台variantinstructions 的功能。
    
    :param platform: 参数 platform（类型: str）
    :return: 返回 str 结果
    """
    tone = {
        "百家号": "偏技术稿，少 emoji，标题含品类+场景，避免营销腔",
        "知乎": "问答体，先给结论再列参数，可带「谢邀」式开头",
        "头条号": "前 80 字给结论和数据，短段",
        "小红书": "工程采购笔记，清单体，emoji 适量",
        "LinkedIn": "Professional English, spec-first, include MOQ and lead time",
        "YouTube": "Video description with timestamps, key specs in first 3 lines",
        "抖音": "口播脚本感，60 秒，3 个数字点",
        # v3 新增 — AI 搜索引擎适配
        "DeepSeek": "技术深度，参数表格，FAQ 格式，引用国标",
        "ChatGPT": "English preferred, structured comparison, clear H2 sections",
        "Gemini": "Concise answers, bullet points, Schema.org compatible",
        "Perplexity": "Source-rich, citation-heavy, include URLs",
        "百度AI": "中文优先，结构化数据，FAQ 格式，引用权威来源",
    }.get(platform, f"适配{platform}，保留参数与 CTA")
    return (
        f"平台：{platform}。{tone}。\n"
        "禁止 AI 套话；保留可验证数据；CTA 指向独立域询盘/电话。\n"
        "v3 要求：品牌名+品类+地域首段锚定；FAQ 格式必备。"
    )


def _count_verifiable_stats(text: str) -> int:
    """实现 数量verifiablestats 的功能。
    
    :param text: 参数 text（类型: str）
    :return: 返回 int 结果
    """
    patterns = [
        r"\d+\.?\d*\s*(?:W/(?:m·K|m\^2·K)|kg/m³|mm|MPa|℃|%)",
        r"\d+\s*(?:元|块|吨|立方|柜|天|个工作日)",
        r"(?:GB/T|JGJ|ASTM|EN|ISO)\s*[-\d]+",
        r"\d{4}年",
        r"MOQ\s*[:：]?\s*\d+",
        # v3 新增 — 价格区间、货期、包装规格
        r"\d+[-–]\d+\s*(?:元|USD|\$|RMB)",
        r"\d+\s*(?:天|个工作日)\s*(?:交货|发货|到货)",
        r"\d+\s*(?:吨|立方|件|包|袋)/?(?:车|柜|托盘)?",
    ]
    return sum(len(re.findall(p, text, re.I)) for p in patterns)


def _count_ai_phrases(text: str) -> int:
    """实现 数量aiphrases 的功能。
    
    :param text: 参数 text（类型: str）
    :return: 返回 int 结果
    """
    count = 0
    for phrase in AI_TASTE_PHRASES:
        if ".*" in phrase:
            count += len(re.findall(phrase, text))
        else:
            count += text.count(phrase)
    return count


def _sentence_length_variance(text: str) -> float:
    """实现 sentencelengthvariance 的功能。
    
    :param text: 参数 text（类型: str）
    :return: 返回 float 结果
    """
    parts = re.split(r"[。！？.!?]", text)
    lengths = [len(p.strip()) for p in parts if len(p.strip()) > 4]
    if len(lengths) < 3:
        return 0.0
    mean = sum(lengths) / len(lengths)
    var = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    return math.sqrt(var)


def _calc_faq_absorption(text: str) -> float:
    """计算 FAQ 格式优化度（arXiv 2604.25707: FAQ 引用吸收率 3x）"""
    score = 0.0
    # 检测 FAQ 格式
    faq_patterns = [
        r"问[：:].{5,80}答[：:]",      # 中文 Q:/A:
        r"Q[：:].{5,80}A[：:]",         # 英文 Q:/A:
        r"\*\*Q[:：].*\*\*.*\n.*A[:：]", # Markdown bold Q/A
        r"问：.*\n.*答：",               # 换行格式
    ]
    faq_count = sum(len(re.findall(p, text, re.M)) for p in faq_patterns)
    score += min(0.5, faq_count * 0.15)
    # FAQ 答案长度在 50-120 字（最佳吸收区间）
    answers = re.findall(r"答[：:](.{50,120})", text)
    if answers:
        score += min(0.3, len(answers) * 0.1)

    # 列表/表格格式（AI Overview 偏好）
    if re.search(r"^[-•·]\s", text, re.M):
        score += 0.1
    if re.search(r"\|.*\|.*\|", text):
        score += 0.1

    return min(1.0, score)


def _calc_brand_anchoring(text: str) -> float:
    """计算品牌锚定度（arXiv 2606.20065: 品牌+品类+地域 提及率+40%）"""
    score = 0.0
    # 品牌名出现
    if re.search(r"[A-Z][a-zA-Z]{2,}|[一-鿿]{2,}(?:建材|混凝土|保温)", text):
        score += 0.3
    # 品类关键词
    categories = ["混凝土", "保温", "防水", "砌块", "砂浆", "岩棉", "混凝土", "concrete", "insulation"]
    if any(c in text.lower() for c in categories):
        score += 0.2
    # 地域锚定
    regions = ["廊坊", "大城", "河北", "山东", "广东", "江苏", "浙江", "China", "Hebei"]
    if any(r in text for r in regions):
        score += 0.2
    # 首段三要素（品牌+品类+地域在前 200 字）
    first_200 = text[:200]
    anchor_hits = sum(1 for pat in [r"[一-鿿]{2,}建材", r"混凝土|保温|防水", r"廊坊|大城|河北"] if re.search(pat, first_200))
    score += min(0.3, anchor_hits * 0.1)
    return min(1.0, score)


def score_content_quality(content: str, *, intent: str = "") -> ContentQualityScore:
    """综合 GEO 引用分 + AI 味分 + FAQ 吸收分 + 品牌锚定分（v3）。"""
    text = (content or "").strip()
    word_approx = max(len(text) // 2, 1)
    stats = _count_verifiable_stats(text)
    stat_density = round(stats / max(word_approx / 200, 1), 2)
    ai_hits = _count_ai_phrases(text)
    ai_taste = min(1.0, ai_hits * 0.08 + (0.15 if stat_density < 0.5 else 0))
    var = _sentence_length_variance(text)
    if var < 8:
        ai_taste = min(1.0, ai_taste + 0.12)

    human_hits = sum(1 for t in HUMAN_SIGNAL_TERMS if t in text)
    human_signal = min(1.0, human_hits / 6)
    # GEO 引用分（原有）
    geo_parts = [
        min(1.0, stat_density / 2),
        0.15 if re.search(r"[「『""].{8,40}[」』""]", text) else 0,
        0.15 if re.search(r"https?://", text) else 0,
        0.1 if re.search(r"(?:GB/T|JGJ|ASTM|EN|ISO)", text) else 0,
        human_signal * 0.2,
    ]
    geo_citation = round(min(1.0, sum(geo_parts)), 4)
    # v3 新增：FAQ 吸收分
    faq_absorption = _calc_faq_absorption(text)
    # v3 新增：品牌锚定分
    brand_anchoring = _calc_brand_anchoring(text)
    reasons: list[str] = []
    if ai_taste >= 0.35:
        reasons.append("ai_taste_high")
    if stat_density < 0.8:
        reasons.append("low_stat_density")
    if human_signal < 0.3:
        reasons.append("low_human_signal")
    if faq_absorption < 0.2:
        reasons.append("low_faq_format")
    if brand_anchoring < 0.3:
        reasons.append("weak_brand_anchor")

    # v3 通过条件（更严格）
    passed = (
        ai_taste < 0.35
        and geo_citation >= 0.40
        and stat_density >= 0.5
        and faq_absorption >= 0.15
        and brand_anchoring >= 0.2
    )
    return ContentQualityScore(
        geo_citation_score=geo_citation,
        ai_taste_score=round(ai_taste, 4),
        human_signal_score=round(human_signal, 4),
        stat_density=stat_density,
        faq_absorption_score=round(faq_absorption, 4),
        brand_anchoring_score=round(brand_anchoring, 4),
        passed=passed,
        reasons=reasons,
    )


def content_quality_to_dict(score: ContentQualityScore) -> dict[str, Any]:
    """实现 内容qualityto字典 的功能。
    
    :param score: 参数 score（类型: ContentQualityScore）
    :return: 返回 dict[str, Any] 结果
    """
    return {
        "geo_citation_score": score.geo_citation_score,
        "ai_taste_score": score.ai_taste_score,
        "human_signal_score": score.human_signal_score,
        "stat_density": score.stat_density,
        "faq_absorption_score": score.faq_absorption_score,
        "brand_anchoring_score": score.brand_anchoring_score,
        "passed": score.passed,
        "reasons": score.reasons,
        "tactics_version": score.tactics_version,
    }
