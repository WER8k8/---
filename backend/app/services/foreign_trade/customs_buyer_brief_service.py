"""海关/买家情报 brief — 公开统计 + playbook，禁止无来源 buyer 列表落库。"""

from __future__ import annotations

from typing import Any

from app.services.trade_intel_data import search_customs
from app.services.trade_intel_service import DISCLAIMER as TRADE_DISCLAIMER


def build_customs_buyer_brief(
    *,
    product: str,
    hs_code: str | None = None,
    country_code: str | None = None,
    limit: int = 8,
    include_sidecar: bool = False,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """CustomsDataSpider 对标：出口统计来自 M1 公开数据；历史采购商须 Sidecar。"""
    query = " ".join(x for x in (product, hs_code or "") if x).strip() or product
    hits = search_customs(query=query, limit=limit)
    if country_code:
        cc = country_code.upper()[:2]
        hits = [h for h in hits if h.get("country_code") == cc] or hits

    sidecar_pack: dict[str, Any] | None = None
    if include_sidecar:
        from app.services.foreign_trade.customs_data_spider_sidecar import fetch_customs_buyer_research
        sidecar_pack = fetch_customs_buyer_research(
            product=product,
            hs_code=hs_code,
            country_code=country_code,
            tenant_id=tenant_id,
            max_results=limit,
        )

    playbook = [
        "用 HS/品名在公开海关统计中看目标国出口指数与同比",
        "CustomsDataSpider 等 Sidecar 仅作 research brief，included 无 source 不得落库",
        "竞品客户反查须租户书面授权 + 合规确认",
        "签约前请报关行/律师确认税号与认证",
    ]
    buyer_history = None
    included = None
    upstream_status = "reference_only"
    if sidecar_pack and sidecar_pack.get("buyers"):
        buyer_history = sidecar_pack["buyers"]
        included = sidecar_pack.get("included")
        upstream_status = "sidecar_stub" if sidecar_pack.get("probe_mode") == "stub" else "sidecar_live"

    return {
        "product": product,
        "hs_code": hs_code,
        "country_code": (country_code or "").upper()[:2] or None,
        "export_market_stats": hits[:limit],
        "stats_count": len(hits),
        "buyer_history": buyer_history,
        "included": included,
        "upstream_sidecar": "CustomsDataSpider",
        "upstream_status": upstream_status,
        "sidecar_meta": (
            {
                "buyer_count": sidecar_pack.get("buyer_count"),
                "probe_mode": sidecar_pack.get("probe_mode"),
                "human_verify_required": sidecar_pack.get("human_verify_required", True),
            }
            if sidecar_pack
            else None
        ),
        "playbook": playbook,
        "disclaimer": TRADE_DISCLAIMER,
        "honesty": (
            "本接口仅返回公开统计与 playbook；未配置 Sidecar 时不返回历史采购商名单。"
            if not buyer_history
            else "Sidecar 买家线索须人工核实 evidence_url；禁止无授权触达。"
        ),
        "next_steps": [
            "配置 DeerFlow brief 模板 customs_trade_intel",
            "部署 CustomsDataSpider Sidecar 后 POST /integrations/customs/buyer-research",
        ],
    }
