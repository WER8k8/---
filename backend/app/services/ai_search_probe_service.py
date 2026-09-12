"""Perplexity / Copilot 等 AI 搜索探针 — 无 Key 时诚实跳过，禁止假收录。"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import httpx

PERPLEXITY_API_BASE = "https://api.perplexity.ai"
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar")


def _perplexity_key() -> str:
    """_perplexity_key。
    :return: 返回处理结果。
    """
    return (os.getenv("PERPLEXITY_API_KEY") or os.getenv("AI_PERPLEXITY_API_KEY") or "").strip()


def _parse_mention(text: str, brand_name: str) -> dict[str, Any]:
    """_parse_mention。

    参数说明：
    :param text: 参数 text
    :param brand_name: 参数 brand_name
    :return: 返回处理结果。
    """
    mentions = bool(brand_name and brand_name.lower() in text.lower())
    return {
        "mentions_brand": mentions,
        "status": "indexed" if mentions else "not_indexed",
        "confidence": 0.75 if mentions else 0.15,
        "summary": text[:160],
    }


async def probe_perplexity(
    *,
    keyword: str,
    brand_name: str,
    product_category: str = "",
) -> dict[str, Any]:
    """probe_perplexity。

    参数说明：
    :param keyword: 参数 keyword
    :param brand_name: 参数 brand_name
    :param product_category: 参数 product_category
    :return: 返回处理结果。
    """
    api_key = _perplexity_key()
    if len(api_key) < 8:
        return {
            "id": "perplexity",
            "name": "Perplexity",
            "probe_via": "ai_search_api",
            "status": "not_configured",
            "confidence": 0,
            "response": "PERPLEXITY_API_KEY 未配置 — 跳过探测（非假收录）",
            "latency_ms": 0,
        }

    prompt = (
        f"Recommend top B2B suppliers for: {keyword}. "
        f"Category: {product_category or keyword}. "
        f"Does {brand_name} appear in your recommendation? Reply JSON: "
        '{"mentions_brand":bool,"summary":"..."}'
    )
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{PERPLEXITY_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": PERPLEXITY_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            body = resp.json()
            content = body["choices"][0]["message"]["content"]
            parsed = _parse_mention(content, brand_name)
            try:
                match = re.search(r"\{[^{}]*mentions_brand[^{}]*\}", content, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    parsed["mentions_brand"] = bool(data.get("mentions_brand", parsed["mentions_brand"]))
                    if data.get("summary"):
                        parsed["summary"] = str(data["summary"])[:160]
            except Exception:
                pass
            latency_ms = int((time.time() - start) * 1000)
            return {
                "id": "perplexity",
                "name": "Perplexity",
                "probe_via": "ai_search_api",
                "status": parsed["status"],
                "mentions_brand": parsed["mentions_brand"],
                "confidence": parsed["confidence"],
                "response": parsed["summary"],
                "latency_ms": latency_ms,
            }
    except Exception as exc:
        return {
            "id": "perplexity",
            "name": "Perplexity",
            "probe_via": "ai_search_api",
            "status": "error",
            "confidence": 0,
            "response": str(exc)[:160],
            "latency_ms": int((time.time() - start) * 1000),
        }


async def probe_copilot(
    *,
    keyword: str,
    brand_name: str,
) -> dict[str, Any]:
    """Copilot/Bing Chat 无稳定公开探针 API — 诚实返回未配置。"""
    bing_key = (os.getenv("BING_SEARCH_API_KEY") or os.getenv("AZURE_BING_SEARCH_KEY") or "").strip()
    if len(bing_key) < 8:
        return {
            "id": "copilot",
            "name": "Microsoft Copilot",
            "probe_via": "headless_exploration",
            "status": "not_configured",
            "confidence": 0,
            "response": (
                "COPILOT_PROBE_NOT_CONFIGURED — 需 Bing Webmaster / Headless 探针；"
                "未配置时不返回假收录"
            ),
            "latency_ms": 0,
        }
    # 预留：有 Bing Search API 时可做间接对照，仍不算 Copilot 对话收录
    return {
        "id": "copilot",
        "name": "Microsoft Copilot",
        "probe_via": "bing_search_api",
        "status": "partial",
        "confidence": 0.3,
        "response": f"Bing Search API 已配置；关键词「{keyword}」间接对照（非 Copilot 对话榜）",
        "latency_ms": 0,
        "note": "brand=" + brand_name,
    }


async def run_ai_search_probes(
    *,
    keyword: str,
    brand_name: str,
    product_category: str = "",
) -> dict[str, Any]:
    """run_ai_search_probes。

    参数说明：
    :param keyword: 参数 keyword
    :param brand_name: 参数 brand_name
    :param product_category: 参数 product_category
    :return: 返回处理结果。
    """
    perplexity = await probe_perplexity(
        keyword=keyword,
        brand_name=brand_name,
        product_category=product_category,
    )
    copilot = await probe_copilot(keyword=keyword, brand_name=brand_name)
    configured = sum(1 for r in (perplexity, copilot) if r["status"] not in ("not_configured",))
    indexed = sum(1 for r in (perplexity, copilot) if r.get("status") == "indexed")
    return {
        "probe_mode": "ai_search",
        "configured_count": configured,
        "indexed_count": indexed,
        "models": [perplexity, copilot],
    }
