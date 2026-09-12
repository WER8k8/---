"""AnySearch 外网探测 — Hermes 研究员 hourly / 批量脚本共用。"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ANYSEARCH_CLI = Path.home() / ".cursor" / "skills" / "anysearch" / "scripts" / "anysearch_cli.py"

# topic_key → 实时检索 query（与 HOURLY_TOPICS 对齐）
TOPIC_ANYSEARCH_QUERIES: dict[str, str] = {
    "geo_rank": "B2B GEO generative engine optimization AI citation 2026",
    "aeo_citation": "AEO AI citation B2B SaaS fact consistency 2026",
    "matrix_publish": "B2B social media matrix multi-platform publish SaaS 2026",
    "content_variants": "content repurposing B2B export one to many platforms",
    "paid_attribution": "B2B marketing UTM attribution inquiry pipeline",
    "market_research": "China export manufacturer overseas market opportunity 2026",
    "competitor_cf_b2b": "B2B export marketing SaaS SEO GEO competitor",
    "ads_creative": "Google Ads Meta B2B lead generation automation",
    "linkedin_b2b": "LinkedIn B2B manufacturing export content strategy",
    "site_onboarding": "B2B website ICP onboarding export manufacturer",
    "outreach_quality": "B2B cold email deliverability SPF DKIM 2026",
    "inquiry_crm": "B2B export inquiry MEDDPICC CRM pipeline",
    "buyer_scout": "AI B2B prospecting human verification export",
    "rfq_negotiation": "B2B RFQ negotiation export manufacturer",
    "email_warmup": "email domain warmup SPF DKIM DMARC B2B",
    "pipeline_forecast": "B2B sales pipeline forecast win strategy",
    "digital_products_landscape": "sell digital products online 2026 Gumroad Paddle templates courses",
    "ai_agent_monetization": "AI agent monetization workflow make money autonomous agents 2026",
    "cursor_mcp_agent_stack": "Cursor MCP agent workflow orchestration subagents developer 2026",
    "n8n_automation_business": "n8n make.com sell automation workflows digital products agency",
    "indie_hacker_ai_stack": "indie hacker AI SaaS micro product launch stack solo founder 2026",
    "affiliate_digital_funnel": "affiliate marketing digital product funnel B2B SaaS lead magnet",
    "agent_swarm_pm_orchestration": "multi agent orchestration PM swarm LangGraph CrewAI monetization",
    "tutorial_agent_playbooks": "AI agent tutorial workflow step by step automation business playbook",
}


def parse_anysearch_output(text: str) -> list[dict[str, str]]:
    """parse_anysearch_output。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    hits: list[dict[str, str]] = []
    pattern = re.compile(
        r"###\s*\d+\.\s*(.+?)\r?\n- \*\*URL\*\*:\s*(.+?)\r?\n(.*?)(?=\r?\n###\s*\d+\.|\Z)",
        re.S,
    )
    for m in pattern.finditer(text):
        title = m.group(1).strip()
        url = m.group(2).strip()
        body = m.group(3).strip()
        snippet = ""
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("- **") or not line:
                continue
            snippet = line[:400]
            break
        hits.append({"title": title[:200], "url": url[:500], "snippet": snippet})
    return hits


def run_anysearch(
    query: str,
    *,
    max_results: int = 5,
    timeout_sec: int = 90,
) -> dict[str, Any]:
    """run_anysearch。

    参数说明：
    :param query: 参数 query
    :param max_results: 参数 max_results
    :param timeout_sec: 参数 timeout_sec
    :return: 返回处理结果。
    """
    if not ANYSEARCH_CLI.is_file():
        return {"ok": False, "error": "anysearch_cli_missing", "query": query, "hits": []}
    cmd = [
        sys.executable,
        str(ANYSEARCH_CLI),
        "search",
        query,
        "--max_results",
        str(max_results),
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
        )
        text = (proc.stdout or "") + (proc.stderr or "")
        hits = parse_anysearch_output(text)[:max_results]
        return {
            "ok": proc.returncode == 0 and bool(hits),
            "query": query,
            "hit_count": len(hits),
            "hits": hits,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "query": query, "hits": []}
    except OSError as exc:
        return {"ok": False, "error": str(exc)[:200], "query": query, "hits": []}


def topic_search_query(topic_key: str, *, label: str = "") -> str:
    """topic_search_query。

    参数说明：
    :param topic_key: 参数 topic_key
    :param label: 参数 label
    :return: 返回处理结果。
    """
    q = TOPIC_ANYSEARCH_QUERIES.get(topic_key)
    if q:
        return q
    base = label or topic_key.replace("_", " ")
    return f"B2B export foreign trade {base} 2026"


def synthesize_finding_extension(base_finding: str, anysearch: dict[str, Any]) -> str:
    """synthesize_finding_extension。

    参数说明：
    :param base_finding: 参数 base_finding
    :param anysearch: 参数 anysearch
    :return: 返回处理结果。
    """
    hits = anysearch.get("hits") or []
    if not hits:
        return f"{base_finding} AnySearch 未返回结果，维持内信号结论。"
    top = hits[0]
    ext = f"外网（AnySearch）：「{top.get('title', '')[:80]}」— {top.get('snippet', '')[:180]}"
    if any(k in ext for k in ("迈富时", "Marketingforce", "marketingforce")):
        ext += " 对标：闭源 SaaS 全链路 vs 本仓 Agent+人审+可部署源码。"
    return f"{base_finding} {ext}"


def enrich_brief_with_anysearch(brief: dict[str, Any], *, max_hits: int = 2) -> dict[str, Any]:
    """只读外网 enrichment；不触发发信/发布/写业务表。"""
    topic_key = brief.get("topic_key") or ""
    query = topic_search_query(topic_key, label=str(brief.get("topic_label") or ""))
    anysearch = run_anysearch(query)
    base = brief.get("finding") or ""
    brief = dict(brief)
    brief["finding"] = synthesize_finding_extension(base, anysearch)
    brief["anysearch"] = anysearch
    brief["research_query"] = query
    evidence = list(brief.get("evidence") or [])
    for h in (anysearch.get("hits") or [])[:max_hits]:
        evidence.append({"type": "anysearch", "ref": h.get("url") or h.get("title"), "value": "web"})
    brief["evidence"] = evidence
    if anysearch.get("hit_count"):
        brief["confidence"] = "high"
    return brief
