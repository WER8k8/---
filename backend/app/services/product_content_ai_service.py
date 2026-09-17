# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""产品页 AI 生成/润色 — 走 NVIDIA NIM 场景模型（invoke_llm）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.ai_invocation_service import invoke_llm


def _product_info_block(payload: dict[str, Any]) -> str:
    """_product_info_block。

    参数说明：
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    lines: list[str] = []
    mapping = [
        ("product_name", "产品名称"),
        ("category_name", "产品分类"),
        ("density", "干密度", " kg/m³"),
        ("strength_grade", "强度等级"),
        ("thermal_conductivity", "导热系数", " W/m·K"),
        ("fire_rating", "防火等级"),
    ]
    for item in mapping:
        key = item[0]
        label = item[1]
        suffix = item[2] if len(item) > 2 else ""
        val = payload.get(key)
        if val not in (None, "", 0):
            lines.append(f"{label}：{val}{suffix}")
    return "\n".join(lines)


def _extract_text(result: dict[str, Any]) -> str:
    """_extract_text。

    参数说明：
    :param result: 参数 result
    :return: 返回处理结果。
    """
    for key in ("content", "optimized_content", "text"):
        val = result.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


async def generate_product_content(
    db: Session,
    *,
    payload: dict[str, Any],
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """generate_product_content。

    参数说明：
    :param db: 参数 db
    :param payload: 参数 payload
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    content_type = str(payload.get("content_type") or "product")
    keywords = payload.get("keywords") or []
    kw = ", ".join(str(k) for k in keywords if k)
    product_name = str(payload.get("product_name") or "")
    category_name = str(payload.get("category_name") or "")
    existing_description = str(payload.get("existing_description") or "")
    info = _product_info_block(payload)
    if content_type == "seo_title":
        prompt = f"""请根据以下建材产品信息生成 SEO 标题（30-60 字，一行输出，不要引号）：

产品名称：{product_name}
产品分类：{category_name}
强度等级：{payload.get('strength_grade') or '—'}
防火等级：{payload.get('fire_rating') or '—'}

要求：含核心关键词；突出卖点；适合百度/Google 检索；诚实不夸大。"""
        scenario = "article"
    elif content_type == "seo_description":
        prompt = f"""请根据以下建材产品信息生成 SEO 描述（80-160 字，一段，不要标题）：

{info}
产品描述摘要：{existing_description[:300]}

要求：含 {product_name}、{category_name}；突出节能/防火/规格；语句自然；诚实不夸大。"""
        scenario = "article"
    else:
        prompt = f"""请为以下建材产品生成专业产品描述（300-500 字，分段）：

{info}
关键词：{kw or product_name}

要求：与产品名称严格相关；含技术参数；引用常见行业标准表述；适合 B2B 官网；诚实不夸大。"""
        scenario = "article"

    result = await invoke_llm(
        db,
        prompt=prompt,
        scenario=scenario,
        max_tokens=1200,
        tenant_id=tenant_id,
        lane="customer",
        task_type=f"product:{content_type}",
    )
    text = _extract_text(result)
    if not text:
        raise RuntimeError("AI 未返回可用内容")
    return {
        "content": text,
        "mock": False,
        "scenario": result.get("scenario") or scenario,
        "model_name": result.get("model_name"),
    }


async def polish_product_content(
    db: Session,
    *,
    content: str,
    polish_type: str = "general",
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """polish_product_content。

    参数说明：
    :param db: 参数 db
    :param content: 参数 content
    :param polish_type: 参数 polish_type
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    body = (content or "").strip()
    if not body:
        raise ValueError("内容不能为空")

    style = {
        "professional": "更专业正式、B2B 建材用语",
        "concise": "更精简、信息密度更高",
        "seo": "更利于 SEO，自然融入建材关键词",
        "emotional": "更有感染力但仍保持工厂直销可信度",
    }.get(polish_type, "更流畅易读")
    prompt = f"""请润色以下建材产品文案（{style}），直接输出润色后正文，不要解释：

{body}

要求：保持事实不变；不编造认证/参数；语法正确。"""
    result = await invoke_llm(
        db,
        prompt=prompt,
        scenario="article",
        max_tokens=1200,
        tenant_id=tenant_id,
        lane="customer",
        task_type="product:polish",
    )
    text = _extract_text(result)
    if not text:
        raise RuntimeError("AI 未返回可用内容")
    return {
        "content": text,
        "mock": False,
        "scenario": result.get("scenario") or "article",
        "model_name": result.get("model_name"),
    }
