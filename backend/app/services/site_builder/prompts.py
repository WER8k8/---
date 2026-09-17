# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""一键建站各步骤 Prompt 模板。

每个步骤有独立的 system / user prompt 组合，用于驱动 LLM 完成特定子任务。
"""

from __future__ import annotations

import json
from typing import Any

# ---------------------------------------------------------------------------
# Step 1: Vision 分析产品图片
# ---------------------------------------------------------------------------

VISION_SYSTEM_PROMPT = """你是建材行业产品视觉分析专家。根据产品图片，提取以下信息并以 JSON 输出：
- product_name: 产品通用名
- category: 产品大类（如保温材料、防水材料、混凝土等）
- features: 产品特性列表（每项一句话）
- parameters: 技术参数（密度/导热系数/防火等级等，能识别则填，否则留 null）
- application_scenarios: 应用场景列表
- visual_notes: 外观与工艺备注

只输出 JSON 对象，不要 markdown 代码块。"""


def build_vision_user_prompt(product_description_text: str, image_count: int) -> str:
    """实现 构建vision用户prompt 的功能。
    
    :param product_description_text: 参数 product_description_text（类型: str）
    :param image_count: 参数 image_count（类型: int）
    :return: 返回 str 结果
    """
    desc_block = f"\n补充文字描述：{product_description_text}" if product_description_text else ""
    return (
        f"以下是 {image_count} 张产品图片。请分析并提取产品信息。{desc_block}\n"
        "输出格式示例：\n"
        '{"product_name": "", "category": "", "features": [], "parameters": {}, "application_scenarios": [], "visual_notes": ""}'
    )


# ---------------------------------------------------------------------------
# Step 2: 生成网站结构
# ---------------------------------------------------------------------------

STRUCTURE_SYSTEM_PROMPT = """你是 B2B 外贸官网架构专家。根据产品信息，确定网站需要哪些页面以及每页的核心内容板块。
输出 JSON，包含 pages 数组，每项含 page_type / slug / title / sections。

标准页面类型：home, products, about, contact, faq, solutions, case-study, downloads
不是每个站点都需要全部页面，请根据产品特性决定（最少 3 页，最多 8 页）。"""


def build_structure_user_prompt(
    product_info: dict[str, Any],
    target_market: str,
    language: str,
) -> str:
    """实现 构建structure用户prompt 的功能。
    
    :param product_info: 参数 product_info（类型: dict[str, Any]）
    :param target_market: 参数 target_market（类型: str）
    :param language: 参数 language（类型: str）
    :return: 返回 str 结果
    """
    info_json = json.dumps(product_info, ensure_ascii=False, indent=2)
    return (
        f"产品信息：\n{info_json}\n\n"
        f"目标市场：{target_market}\n"
        f"站点语言：{language}\n\n"
        "请生成网站结构。输出格式示例：\n"
        '{"pages": [{"page_type": "home", "slug": "index", "title": "...", "sections": ["hero", "features", "products", "contact"]}, ...]}'
    )


# ---------------------------------------------------------------------------
# Step 3: 生成多语言内容
# ---------------------------------------------------------------------------

CONTENT_SYSTEM_PROMPT = """你是多语种 B2B 内容创作专家。为每个页面生成指定语言的标题、描述和正文内容。
输出 JSON，每项含 page_type / title / meta_description / content_markdown。
要求：专业、面向目标市场采购商、SEO 友好、不要空话套话。"""


def build_content_user_prompt(
    page: dict[str, Any],
    product_info: dict[str, Any],
    target_market: str,
    language: str,
) -> str:
    """实现 构建内容用户prompt 的功能。
    
    :param page: 参数 page（类型: dict[str, Any]）
    :param product_info: 参数 product_info（类型: dict[str, Any]）
    :param target_market: 参数 target_market（类型: str）
    :param language: 参数 language（类型: str）
    :return: 返回 str 结果
    """
    info_json = json.dumps(product_info, ensure_ascii=False, indent=2)
    page_json = json.dumps(page, ensure_ascii=False, indent=2)
    return (
        f"产品信息：\n{info_json}\n\n"
        f"当前页面定义：\n{page_json}\n\n"
        f"目标市场：{target_market}\n"
        f"内容语言：{language}\n\n"
        "请为该页面生成完整内容。输出格式示例：\n"
        '{"page_type": "home", "title": "...", "meta_description": "...", "content_markdown": "..."}'
    )


# ---------------------------------------------------------------------------
# Step 4: SEO 优化
# ---------------------------------------------------------------------------

SEO_SYSTEM_PROMPT = """你是国际 SEO 专家。为每个页面生成 SEO 元数据。
输出 JSON，每项含 page_type / seo_title / seo_keywords / schema_type / internal_links。
要求：keywords 3-5 个；seo_title 不超过 60 字符；schema 类型从 Article / Product / FAQPage / Organization 选。"""


def build_seo_user_prompt(
    page: dict[str, Any],
    page_content: dict[str, Any],
    all_pages: list[dict[str, Any]],
    product_info: dict[str, Any],
) -> str:
    """实现 构建seo用户prompt 的功能。
    
    :param page: 参数 page（类型: dict[str, Any]）
    :param page_content: 参数 page_content（类型: dict[str, Any]）
    :param all_pages: 参数 all_pages（类型: list[dict[str, Any]]）
    :param product_info: 参数 product_info（类型: dict[str, Any]）
    :return: 返回 str 结果
    """
    product_json = json.dumps(product_info, ensure_ascii=False, indent=2)
    content_json = json.dumps(page_content, ensure_ascii=False, indent=2)
    pages_json = json.dumps(all_pages, ensure_ascii=False, indent=2)
    return (
        f"产品信息：\n{product_json}\n\n"
        f"当前页面内容：\n{content_json}\n\n"
        f"全部页面列表（供内链参考）：\n{pages_json}\n\n"
        "请为该页面生成 SEO 元数据。输出格式示例：\n"
        '{"page_type": "home", "seo_title": "...", "seo_keywords": ["k1","k2"], "schema_type": "Organization", "internal_links": [{"target_slug": "products", "anchor": "查看产品"}]}'
    )
