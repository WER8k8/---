#!/usr/bin/env python3
"""Hermes 十轮研究：AnySearch 外网采集 + 研究员 Brief + ECC + 部门路由。

用法（仓库根目录）:
  python scripts/run-hermes-anysearch-research-rounds.py
  python scripts/run-hermes-anysearch-research-rounds.py --plan gwl --rounds 5
  python scripts/run-hermes-anysearch-research-rounds.py --rounds 10 --focus marketingforce

输出:
  --plan seo_geo (默认) → .project/hermes-anysearch-10rounds-latest.json
  --plan gwl           → .project/hermes-anysearch-gwl5rounds-latest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

ANYSEARCH_CLI = Path.home() / ".cursor" / "skills" / "anysearch" / "scripts" / "anysearch_cli.py"
OUT_PATH_SEO = ROOT / ".project" / "hermes-anysearch-10rounds-latest.json"
OUT_PATH_GWL = ROOT / ".project" / "hermes-anysearch-gwl5rounds-latest.json"
OUT_PATH_MONETIZE = ROOT / ".project" / "hermes-anysearch-monetize-latest.json"

# 十轮主题：SEO/GEO/出海 + 迈富时对标 + 本仓 lane
ROUND_PLAN: tuple[dict[str, str], ...] = (
    {
        "key": "geo_rank",
        "lane": "GW-G",
        "label": "GEO 排名与 AEO 可见性",
        "category": "geo_rank",
        "query": "迈富时 Marketingforce GEO 生成式引擎优化 T-GEO 2026",
    },
    {
        "key": "aeo_citation",
        "lane": "GW-G",
        "label": "AI 引文与站点事实一致",
        "category": "geo_rank",
        "query": "B2B 外贸 AEO GEO AI citation optimization SaaS 2026",
    },
    {
        "key": "matrix_publish",
        "lane": "GW-S",
        "label": "矩阵发帖与平台绑定",
        "category": "structured_data",
        "query": "外贸 社媒矩阵 多平台发布 SaaS LinkedIn 抖音 2026",
    },
    {
        "key": "content_variants",
        "lane": "GW-G",
        "label": "1→N 内容变体",
        "category": "frontend",
        "query": "content repurposing B2B export marketing one to many platforms",
    },
    {
        "key": "paid_attribution",
        "lane": "GW-P",
        "label": "UTM 归因与付费漏斗",
        "category": "performance",
        "query": "B2B marketing UTM attribution inquiry pipeline SaaS",
    },
    {
        "key": "market_research",
        "lane": "GW-R",
        "label": "迈富时外贸战略与第二曲线",
        "category": "paper",
        "query": "迈富时 T云外贸版 出海 收入增长 2025 2026",
    },
    {
        "key": "competitor_cf_b2b",
        "lane": "GW-PM",
        "label": "外贸营销 SaaS 竞品对照",
        "category": "paper",
        "query": "外贸独立站 营销云 SEO GEO 竞品 中小外贸企业",
    },
    {
        "key": "ads_creative",
        "lane": "GW-P",
        "label": "广告创意与真投放差距",
        "category": "performance",
        "query": "Google Ads Meta B2B export lead generation automation 2026",
    },
    {
        "key": "linkedin_b2b",
        "lane": "GW-S",
        "label": "LinkedIn B2B 出海内容",
        "category": "paper",
        "query": "LinkedIn B2B manufacturing export content strategy 2026",
    },
    {
        "key": "site_onboarding",
        "lane": "GW-G",
        "label": "独立域建站与 ICP onboarding",
        "category": "frontend",
        "query": "B2B website ICP onboarding export manufacturer SaaS",
    },
)


# GW-L 五轮：开发信 / 询盘 / 找客 / 谈单 / 域名预热
ROUND_PLAN_GWL: tuple[dict[str, str], ...] = (
    {
        "key": "outreach_quality",
        "lane": "GW-L",
        "label": "开发信送达与反垃圾箱",
        "category": "paper",
        "query": "B2B cold email deliverability SPF DKIM warmup 2026 best practices",
    },
    {
        "key": "inquiry_crm",
        "lane": "GW-L",
        "label": "询盘评分与 MEDDPICC",
        "category": "structured_data",
        "query": "B2B export inquiry scoring MEDDPICC CRM pipeline SaaS",
    },
    {
        "key": "buyer_scout",
        "lane": "GW-L",
        "label": "找客画像与人工核实",
        "category": "paper",
        "query": "AI B2B prospecting human in the loop verification export manufacturing",
    },
    {
        "key": "rfq_negotiation",
        "lane": "GW-L",
        "label": "RFQ 谈单与成本底线",
        "category": "paper",
        "query": "B2B RFQ negotiation playbook export manufacturer price defense",
    },
    {
        "key": "email_warmup",
        "lane": "GW-L",
        "label": "域名预热与 SPF/DKIM",
        "category": "paper",
        "query": "email domain warmup SPF DKIM DMARC B2B outreach compliance 2026",
    },
)


def _monetize_plan() -> tuple[dict[str, str], ...]:
    import json as _json
    from pathlib import Path as _Path

    p = BACKEND / "app" / "data" / "hermes_marketing_monetize_workflow.json"
    data = _json.loads(p.read_text(encoding="utf-8"))
    rounds = data.get("research_rounds") or []
    return tuple(
        {
            "key": r["key"],
            "lane": r["lane"],
            "label": r["label"],
            "category": r.get("category", "paper"),
            "query": r["query"],
            "decompose_axes": ",".join(r.get("decompose_axes") or []),
        }
        for r in rounds
    )


from app.services.hermes.anysearch_probe_service import (
    run_anysearch,
    synthesize_finding_extension,
    topic_search_query,
)


def _run_round(
    db,
    round_no: int,
    topic: dict[str, str],
    *,
    signals: dict,
) -> dict:
    from app.services.hermes.ecc_expert_panel import review_candidate
    from app.services.hermes.hermes_continuous_iteration_service import (
        brief_to_ecc_candidate,
        route_departments,
    )
    from app.services.hermes.research_brief_service import compose_research_brief

    query = topic.get("query") or topic_search_query(topic["key"], label=topic.get("label", ""))
    anysearch = run_anysearch(query)
    at = datetime.now(timezone.utc)
    brief = compose_research_brief(db, topic=topic, signals=signals, at=at)
    base = brief.get("finding") or ""
    brief["finding"] = synthesize_finding_extension(base, anysearch)
    brief["anysearch"] = anysearch
    brief["round"] = round_no
    brief["research_query"] = query

    evidence = list(brief.get("evidence") or [])
    for h in (anysearch.get("hits") or [])[:2]:
        evidence.append({"type": "anysearch", "ref": h.get("url") or h.get("title"), "value": "web"})
    brief["evidence"] = evidence
    if anysearch.get("hit_count"):
        brief["confidence"] = "high"

    candidate = brief_to_ecc_candidate(brief)
    ecc = review_candidate(db, candidate, allow_llm=False)
    reviews = ecc.get("expert_reviews") or []
    routing = route_departments(brief, ecc_reviews=reviews)
    ecc_verdict = ecc.get("expert_verdict") or "skip"

    a2a_skill = None
    decomposition = None
    try:
        from app.services.hermes.marketing_anysearch_workflow_service import decompose_hits

        decomposition = decompose_hits(
            anysearch.get("hits") or [],
            topic_label=topic.get("label", ""),
        )
    except Exception:
        decomposition = None

    try:
        from app.services.hermes.a2a_skill_marketplace_service import crystallize_a2a_skill

        a2a_skill = crystallize_a2a_skill(
            brief=brief,
            ecc_verdict=ecc_verdict,
            department_routing=routing,
        )
    except Exception:
        a2a_skill = None

    return {
        "round": round_no,
        "topic_key": topic["key"],
        "topic_label": topic["label"],
        "lane": topic["lane"],
        "anysearch_query": query,
        "anysearch_ok": anysearch.get("ok"),
        "anysearch_hits": anysearch.get("hit_count", 0),
        "brief": {
            "brief_id": brief.get("brief_id"),
            "finding": brief.get("finding"),
            "impact": brief.get("impact"),
            "confidence": brief.get("confidence"),
            "suggested_tasks": brief.get("suggested_tasks"),
        },
        "anysearch_hits_detail": anysearch.get("hits") or [],
        "decomposition": decomposition,
        "ecc_verdict": ecc_verdict,
        "ecc_reviews": reviews[:4],
        "departments": routing,
        "a2a_skill": (
            {
                "skill_id": a2a_skill.get("skill_id"),
                "price_credits": a2a_skill.get("price_credits"),
                "invoke_handler": a2a_skill.get("invoke_handler"),
            }
            if a2a_skill
            else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--focus", default="marketingforce")
    parser.add_argument(
        "--plan",
        choices=("seo_geo", "gwl", "monetize"),
        default="seo_geo",
        help="seo_geo=十轮 SEO/GEO/出海；gwl=五轮 GW-L 销售泳道；monetize=八轮数字产品/智能体变现",
    )
    args = parser.parse_args()

    if args.plan == "gwl":
        plan_src = ROUND_PLAN_GWL
        out_path = OUT_PATH_GWL
    elif args.plan == "monetize":
        plan_src = _monetize_plan()
        out_path = OUT_PATH_MONETIZE
    else:
        plan_src = ROUND_PLAN
        out_path = OUT_PATH_SEO

    n = args.rounds if args.rounds is not None else len(plan_src)
    plan = list(plan_src[: max(1, min(n, len(plan_src)))])

    from app.db.session import SessionLocal
    from app.services.hermes.research_brief_service import collect_signals

    db = SessionLocal()
    try:
        signals = collect_signals(db)
        rounds_out: list[dict] = []
        for i, topic in enumerate(plan, start=1):
            print(f"[{i}/{len(plan)}] {topic['label']} …", flush=True)
            rounds_out.append(_run_round(db, i, topic, signals=signals))

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "plan": args.plan,
            "focus": args.focus,
            "rounds_planned": len(plan),
            "anysearch_cli": str(ANYSEARCH_CLI),
            "constitution": "read_probe + suggest_remediation only; no auto mutate",
            "signals_summary": {
                "gw_pending_p0": signals.get("gw_pending_p0_count"),
                "patrol_fail": (signals.get("patrol_summary") or {}).get("fail_count"),
            },
            "rounds": rounds_out,
            "executive_summary": _executive_summary(rounds_out),
        }

        if args.plan == "monetize":
            try:
                from app.services.hermes.marketing_anysearch_workflow_service import (
                    aggregate_workflow_blueprint,
                )

                report["workflow_blueprint"] = aggregate_workflow_blueprint(rounds_out)
                dr = report["workflow_blueprint"].get("deep_read") or {}
                if dr.get("summary"):
                    report["executive_summary"] = (
                        report["executive_summary"] + "\n\n**深度解读**\n" + dr.get("summary", "")
                    )
            except Exception as exc:
                report["workflow_blueprint_error"] = str(exc)[:200]

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {out_path}", flush=True)
        print(report["executive_summary"][:800], flush=True)
        return 0
    finally:
        db.close()


def _executive_summary(rounds: list[dict]) -> str:
    lines = ["## Hermes × AnySearch 十轮研究摘要\n"]
    for r in rounds:
        dept = ", ".join(d.get("seat", "") for d in r.get("departments") or [])
        lines.append(
            f"**R{r['round']} {r['topic_label']}** ({r['lane']}) — "
            f"hits={r.get('anysearch_hits')} ecc={r.get('ecc_verdict')} → {dept}\n"
            f"- {r.get('brief', {}).get('finding', '')[:280]}…\n"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
