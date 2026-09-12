"""付费广告创意 — 结构化变体 + 可选 AI 增强。"""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session


def _template_variants(product: str, budget: float) -> list[dict[str, Any]]:
    """_template_variants。

    参数说明：
    :param product: 参数 product
    :param budget: 参数 budget
    :return: 返回处理结果。
    """
    title = product[:48] or "insulation export"
    return [
        {
            "channel": "google_search",
            "headline": f"Export-grade {title}",
            "description": "Factory direct · MOQ flexible · CE/ISO · inquiry within 24h",
            "budget_usd": budget,
            "cta": "Get quote",
        },
        {
            "channel": "meta_feed",
            "headline": f"建材出口 · {title[:20]}",
            "description": "独立站询盘 · 多语言支持 · 工厂直供",
            "budget_usd": budget,
            "cta": "Learn more",
        },
        {
            "channel": "linkedin_sponsored",
            "headline": f"B2B {title} — OEM/ODM",
            "description": "Project supply · technical docs · global shipping",
            "budget_usd": budget,
            "cta": "Contact sales",
        },
    ]


async def generate_paid_ads_creative(
    db: Session | None,
    *,
    tenant_id: str | None,
    product_hint: str,
    budget_usd: float = 500.0,
    locale: str = "zh",
) -> dict[str, Any]:
    """generate_paid_ads_creative。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param product_hint: 参数 product_hint
    :param budget_usd: 参数 budget_usd
    :param locale: 参数 locale
    :return: 返回处理结果。
    """
    product = (product_hint or "insulation export").strip()
    budget = max(50.0, min(float(budget_usd or 500.0), 100_000.0))
    variants = _template_variants(product, budget)
    source = "template"
    if db is not None and tenant_id:
        try:
            from app.services.ai_key_probe import ai_key_status
            if ai_key_status(db).get("has_real_key"):
                from app.services.ai_invocation_service import invoke_llm
                prompt = (
                    f"Product: {product}. Budget USD {budget:.0f}. "
                    f"Locale: {locale}. "
                    "Return JSON array of 3 ad variants with keys: "
                    "channel, headline, description, cta (max 90 chars each field)."
                )
                result = await invoke_llm(
                    db,
                    prompt=prompt,
                    scenario="article",
                    max_tokens=800,
                    task_type="paid_ads_creative",
                    tenant_id=tenant_id,
                    lane="customer",
                )
                raw = str(result.get("content") or "").strip()
                start = raw.find("[")
                end = raw.rfind("]")
                if start >= 0 and end > start:
                    parsed = json.loads(raw[start : end + 1])
                    if isinstance(parsed, list) and parsed:
                        for row in parsed:
                            if isinstance(row, dict):
                                row.setdefault("budget_usd", budget)
                        variants = parsed[:5]
                        source = "ai"
        except Exception:
            pass

    return {
        "mode": "creative_pack",
        "source": source,
        "budget_usd": budget,
        "product": product,
        "variants": variants,
        "export_formats": ["json", "csv"],
        "human_review_required": True,
        "next_step": "人审后导入 Google Ads / Meta Ads Manager；本系统暂不直连投放 API。",
        "api_note": "P2 可接 Google Ads / Meta Marketing API OAuth",
    }
