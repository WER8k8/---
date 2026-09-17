# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Tavily 外网 AI/SEO 新闻搜索（RADAR-09）。"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("uj-admin.tavily_search")

TAVILY_QUERIES: list[str] = [
    "Generative Engine Optimization GEO citation research 2025 2026",
    "Princeton GEO paper statistics addition AI search visibility",
    "豆包 AI 搜索 排名 优化 GEO",
    "360纳米 AI搜索 推荐机制",
    "百度 文心 大模型 蒸馏 更新 搜索",
    "headless browser AI agent web scraping ranking",
    "LLM agent framework release",
    "Schema.org FAQ structured data AI search",
]


def tavily_configured() -> bool:
    """实现 tavilyconfigured 的功能。
    
    :return: 返回 bool 结果
    """
    key = getattr(settings, "TAVILY_API_KEY", None) or os.getenv("TAVILY_API_KEY")
    return bool((key or "").strip())


def fetch_tavily_search(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """实现 获取tavily搜索 的功能。
    
    :param query: 参数 query（类型: str）
    :param limit: 参数 limit（类型: int）
    :return: 返回 list[dict[str, Any]] 结果
    """
    api_key = (
        getattr(settings, "TAVILY_API_KEY", None) or os.getenv("TAVILY_API_KEY") or ""
    ).strip()
    if not api_key:
        return []
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": min(limit, 10),
        "include_answer": False,
    }
    try:
        with httpx.Client(timeout=20) as client:
            resp = client.post("https://api.tavily.com/search", json=payload)
        if resp.status_code >= 400:
            logger.warning("Tavily HTTP %s: %s", resp.status_code, resp.text[:200])
            return []
        data = resp.json()
    except Exception as exc:
        logger.warning("Tavily fetch failed: %s", exc)
        return []

    out: list[dict[str, Any]] = []
    for row in (data.get("results") or [])[:limit]:
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "title": (row.get("title") or "").strip(),
                "url": row.get("url") or "",
                "source": "tavily",
                "published_at": "",
                "fetch_kind": "tavily_search",
                "body_preview": (row.get("content") or "")[:240],
                "query": query,
            }
        )
    return out


def fetch_tavily_radar_items(
    queries: list[str] | None = None,
    limit_per_query: int = 3,
) -> dict[str, Any]:
    """实现 获取tavilyradar条目 的功能。
    
    :param queries: 参数 queries（类型: list[str] | None）
    :param limit_per_query: 参数 limit_per_query（类型: int）
    :return: 返回 dict[str, Any] 结果
    """
    if not tavily_configured():
        return {"configured": False, "items": [], "errors": []}
    use_queries = queries or TAVILY_QUERIES
    items: list[dict[str, Any]] = []
    errors: list[str] = []
    for q in use_queries:
        try:
            batch = fetch_tavily_search(q, limit=limit_per_query)
            items.extend(batch)
            if not batch:
                errors.append(f"empty:{q}")
        except Exception as exc:
            errors.append(f"{q}:{exc}")
    return {"configured": True, "items": items, "errors": errors}
