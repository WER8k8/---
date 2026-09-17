# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 营销 Lane — AnySearch 数字产品/智能体变现深度拆解与工作流编排。"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.services.hermes.anysearch_probe_service import run_anysearch, synthesize_finding_extension
from app.services.hermes.maintenance_constitution import assert_maintenance_action

logger = logging.getLogger("uj-admin.hermes_marketing_anysearch_workflow")

WORKFLOW_PATH = Path(__file__).resolve().parents[2] / "data" / "hermes_marketing_monetize_workflow.json"
SNAPSHOT_KEY = "hermes:marketing_monetize_workflow:latest"

# 外网 snippet 关键词 → 变现模型 / 栈层 / playbook 步骤
_MODEL_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (r"gumroad|paddle|lemonsqueezy|stripe", "digital_goods_direct", "直售平台"),
    (r"course|template|ebook|pdf|download", "digital_goods_direct", "数字下载品"),
    (r"subscription|saas|micro.?saas", "agent_as_service", "订阅/微 SaaS"),
    (r"affiliate|commission|referral", "content_affiliate", "联盟分佣"),
    (r"n8n|make\.com|zapier|automation workflow", "workflow_packaging", "自动化工作流包"),
    (r"mcp|cursor|subagent|orchestrat", "agent_as_service", "Agent 编排栈"),
    (r"langgraph|crewai|swarm|multi.?agent", "agent_as_service", "多智能体编排"),
    (r"human.?in.?the.?loop|human.?review|approve", "agent_as_service", "人审门控"),
    (r"tutorial|playbook|step.?by.?step|how to", "workflow_packaging", "教程型 playbook"),
    (r"lead magnet|funnel|utm|conversion", "content_affiliate", "漏斗转化"),
)

_STACK_LAYERS: tuple[tuple[str, str], ...] = (
    ("discover", r"search|research|discover|anysearch|scrape|osint"),
    ("orchestrate", r"orchestrat|pm|swarm|crew|langgraph|workflow"),
    ("execute", r"agent|automation|run|execute|invoke|tool"),
    ("gate", r"review|ecc|security|compliance|human|approve"),
    ("monetize", r"pay|revenue|sell|pricing|monetiz|earn|affiliate"),
    ("measure", r"analytics|utm|attribution|kpi|metric|dashboard"),
)


@lru_cache(maxsize=1)
def load_monetize_workflow() -> dict[str, Any]:
    """load_monetize_workflow。
    :return: 返回处理结果。
    """
    with open(WORKFLOW_PATH, encoding="utf-8") as f:
        return json.load(f)


def _match_patterns(text: str, patterns: tuple[tuple[str, ...], ...]) -> list[dict[str, str]]:
    """_match_patterns。

    参数说明：
    :param text: 参数 text
    :param patterns: 参数 patterns
    :return: 返回处理结果。
    """
    low = text.lower()
    hits: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in patterns:
        if len(row) == 3:
            pat, model_id, label = row
            if re.search(pat, low, re.I) and model_id not in seen:
                seen.add(model_id)
                hits.append({"model_id": model_id, "label": label, "matched": pat})
        elif len(row) == 2:
            layer_id, pat = row
            if re.search(pat, low, re.I) and layer_id not in seen:
                seen.add(layer_id)
                hits.append({"layer_id": layer_id, "matched": pat})
    return hits


def decompose_hits(hits: list[dict[str, str]], *, topic_label: str = "") -> dict[str, Any]:
    """从 AnySearch hits 深度拆解变现模型与工作流栈层。"""
    blob = " ".join(
        f"{h.get('title', '')} {h.get('snippet', '')} {h.get('url', '')}" for h in hits
    )
    models = _match_patterns(blob, _MODEL_PATTERNS)
    layers = _match_patterns(blob, _STACK_LAYERS)
    playbook_steps: list[dict[str, str]] = []
    for i, h in enumerate(hits[:5], start=1):
        title = (h.get("title") or "")[:100]
        snippet = (h.get("snippet") or "")[:200]
        playbook_steps.append(
            {
                "step": str(i),
                "source_title": title,
                "insight": snippet,
                "url": h.get("url") or "",
                "hermes_mapping": _map_hit_to_hermes(snippet + " " + title),
            }
        )

    return {
        "topic_label": topic_label,
        "models_detected": models,
        "stack_layers_detected": layers,
        "playbook_steps": playbook_steps,
        "hit_count": len(hits),
    }


def _map_hit_to_hermes(text: str) -> str:
    """_map_hit_to_hermes。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    low = text.lower()
    if re.search(r"geo|seo|citation|content", low):
        return "GW-G 营销内容 / geo_content_matrix"
    if re.search(r"email|outbound|sales|crm", low):
        return "GW-L 销售 outbound"
    if re.search(r"paid|ads|utm|funnel", low):
        return "GW-P 付费归因"
    if re.search(r"research|market|brief", low):
        return "GW-R 研究员 Brief"
    if re.search(r"agent|mcp|cursor|orchestr", low):
        return "GW-PM PM 蜂群编排 + ECC 门控"
    return "GW-G 营销 Lane 人工采纳"


def run_monetize_round(
    db: Session | None,
    round_no: int,
    topic: dict[str, Any],
    *,
    signals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """单轮：AnySearch → Brief → 拆解 → ECC → 部门路由。"""
    assert_maintenance_action("read_probe")
    from app.services.hermes.ecc_expert_panel import review_candidate
    from app.services.hermes.hermes_continuous_iteration_service import (
        brief_to_ecc_candidate,
        route_departments,
    )
    from app.services.hermes.research_brief_service import collect_signals, compose_research_brief
    if signals is None:
        signals = collect_signals(db) if db is not None else {}

    query = topic.get("query") or ""
    anysearch = run_anysearch(query, max_results=5)
    at = datetime.now(timezone.utc)
    brief = compose_research_brief(db, topic=topic, signals=signals, at=at)
    base = brief.get("finding") or ""
    brief["finding"] = synthesize_finding_extension(base, anysearch)
    brief["anysearch"] = anysearch
    brief["round"] = round_no
    brief["research_query"] = query
    brief["workflow_plan"] = "monetize"
    hits = anysearch.get("hits") or []
    decomposition = decompose_hits(hits, topic_label=str(topic.get("label") or ""))
    decomposition["decompose_axes"] = topic.get("decompose_axes") or []
    evidence = list(brief.get("evidence") or [])
    for h in hits[:2]:
        evidence.append({"type": "anysearch", "ref": h.get("url") or h.get("title"), "value": "web"})
    brief["evidence"] = evidence
    if anysearch.get("hit_count"):
        brief["confidence"] = "high"

    candidate = brief_to_ecc_candidate(brief)
    ecc = review_candidate(db, candidate, allow_llm=False)
    reviews = ecc.get("expert_reviews") or []
    routing = route_departments(brief, ecc_reviews=reviews)
    ecc_verdict = ecc.get("expert_verdict") or "skip"
    marketing_routing = [r for r in routing if r.get("seat") in ("marketing", "research", "pm")]
    return {
        "round": round_no,
        "topic_key": topic.get("key"),
        "topic_label": topic.get("label"),
        "lane": topic.get("lane"),
        "anysearch_query": query,
        "anysearch_ok": anysearch.get("ok"),
        "anysearch_hits": anysearch.get("hit_count", 0),
        "anysearch_hits_detail": hits,
        "decomposition": decomposition,
        "brief": {
            "brief_id": brief.get("brief_id"),
            "finding": brief.get("finding"),
            "impact": brief.get("impact"),
            "confidence": brief.get("confidence"),
            "suggested_tasks": brief.get("suggested_tasks"),
        },
        "ecc_verdict": ecc_verdict,
        "ecc_reviews": reviews[:4],
        "departments": routing,
        "marketing_seats": marketing_routing,
    }


def aggregate_workflow_blueprint(rounds: list[dict[str, Any]]) -> dict[str, Any]:
    """跨轮汇总：统一变现模型谱系 + 推荐 Hermes 编排 DAG。"""
    wf = load_monetize_workflow()
    model_counts: dict[str, int] = {}
    layer_counts: dict[str, int] = {}
    all_steps: list[dict[str, str]] = []
    for r in rounds:
        dec = r.get("decomposition") or {}
        for m in dec.get("models_detected") or []:
            mid = m.get("model_id") or ""
            model_counts[mid] = model_counts.get(mid, 0) + 1
        for layer in dec.get("stack_layers_detected") or []:
            lid = layer.get("layer_id") or ""
            layer_counts[lid] = layer_counts.get(lid, 0) + 1
        all_steps.extend(dec.get("playbook_steps") or [])

    ranked_models = sorted(model_counts.items(), key=lambda x: -x[1])
    ranked_layers = sorted(layer_counts.items(), key=lambda x: -x[1])
    archetypes = wf.get("reference_archetypes") or []
    recommended = []
    for mid, _ in ranked_models[:4]:
        for a in archetypes:
            if a.get("id") == mid:
                recommended.append(a)
                break

    dag = {
        "nodes": [
            {"id": s["id"], "title": s["title"], "seat": s["seat"], "skill": s["skill"]}
            for s in wf.get("pipeline_stages") or []
        ],
        "edges": [
            {"from": "L1_discover", "to": "L2_synthesize"},
            {"from": "L2_synthesize", "to": "L3_decompose"},
            {"from": "L3_decompose", "to": "L4_ecc"},
            {"from": "L4_ecc", "to": "L5_pm_inbox", "condition": "ecc_verdict != fail"},
            {"from": "L5_pm_inbox", "to": "L6_survival_sidecar", "optional": True},
        ],
    }
    deep_read = _synthesize_deep_read(rounds, ranked_models, ranked_layers)
    return {
        "workflow_version": wf.get("version"),
        "title": wf.get("title"),
        "model_ranking": [{"model_id": k, "round_hits": v} for k, v in ranked_models],
        "stack_layer_ranking": [{"layer_id": k, "round_hits": v} for k, v in ranked_layers],
        "recommended_archetypes": recommended,
        "pipeline_dag": dag,
        "playbook_highlights": all_steps[:12],
        "deep_read": deep_read,
        "hermes_marketing_actions": wf.get("hermes_marketing_actions"),
    }


def _synthesize_deep_read(
    rounds: list[dict[str, Any]],
    ranked_models: list[tuple[str, int]],
    ranked_layers: list[tuple[str, int]],
) -> dict[str, Any]:
    """结构化深度解读（规则合成，可后续接 LLM）。"""
    top_model = ranked_models[0][0] if ranked_models else "digital_goods_direct"
    top_layers = [x[0] for x in ranked_layers[:4]]
    findings: list[str] = []
    for r in rounds:
        finding = (r.get("brief") or {}).get("finding") or ""
        if finding:
            findings.append(f"R{r.get('round')} {r.get('topic_label')}: {finding[:220]}")

    return {
        "summary": (
            "外网信号显示：数字产品与 Agent 变现的主流路径是 "
            "「发现层(搜索/调研) → 编排层(PM/多 Agent) → 执行层(自动化/MCP) → "
            "门控层(人审/合规) → 变现层(直售/订阅/联盟) → 度量层(UTM/KPI)」。"
            f"本轮 AnySearch 最强信号模型：{top_model}；栈层：{', '.join(top_layers) or 'discover,orchestrate'}。"
        ),
        "platform_adaptation": [
            "直售：Research Brief 模板 + 旺财插件 + 可导出 playbook → 数字交付物",
            "Agent 即服务：Hermes hourly Brief + AnySearch 按次 + ECC 门控 → 超管/租户增值",
            "工作流包：本仓 scripts/run-hermes-anysearch + monetize workflow JSON → 可售卖 SOP",
            "联盟漏斗：矩阵内容(GW-S) + UTM(GW-P) → 万里汇 affiliate 入 survival（超管）",
        ],
        "vs_tutorial_agents": [
            "教程型智能体多强调「单 Agent 循环 + 工具调用」；本仓差异在 ECC 八席 + PM Inbox 硬门控",
            "外网 n8n/Make 变现偏「卖模板+代运维」；Hermes 偏「B2B 外贸 SaaS 内嵌 Agent + 人审」",
            "Cursor/MCP 栈与本仓 CodeGraph + AnySearch + Agency 蜂群同构，可打包为开发者数字品",
        ],
        "round_findings": findings,
        "next_human_actions": [
            "PM Inbox 采纳 1–2 条可落地数字品假设（模板/Skill 包/Brief 增值）",
            "营销 Lane 用 matrix_publish 发 1 篇「工作流拆解」引流文（人审后）",
            "财迷疯分身只读映射：哪条通道走 WorldFirst survival vs 租户微信/支付宝",
        ],
    }


def run_monetize_workflow(
    db: Session | None,
    *,
    max_rounds: int | None = None,
    trigger: str = "api",
) -> dict[str, Any]:
    """完整八轮（或截断）营销 AnySearch 变现研究工作流。"""
    assert_maintenance_action("read_probe")
    wf = load_monetize_workflow()
    plan = list(wf.get("research_rounds") or [])
    if max_rounds is not None:
        plan = plan[: max(1, min(max_rounds, len(plan)))]

    from app.services.hermes.research_brief_service import collect_signals
    signals = collect_signals(db) if db is not None else {}
    rounds_out: list[dict] = []
    for i, topic in enumerate(plan, start=1):
        rounds_out.append(run_monetize_round(db, i, topic, signals=signals))

    blueprint = aggregate_workflow_blueprint(rounds_out)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trigger": trigger,
        "plan": "monetize",
        "rounds_planned": len(plan),
        "constitution": "read_probe + suggest_remediation; marketing drives AnySearch; no auto publish",
        "rounds": rounds_out,
        "workflow_blueprint": blueprint,
        "executive_summary": _executive_summary(rounds_out, blueprint),
    }
    assert_maintenance_action("write_patrol_snapshot")
    if redis_client:
        redis_client.set(
            SNAPSHOT_KEY,
            json.dumps(report, ensure_ascii=False),
            ex=86400 * 14,
        )
    return report


def load_monetize_snapshot() -> dict[str, Any] | None:
    """load_monetize_snapshot。
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    if not redis_client:
        return None
    raw = redis_client.get(SNAPSHOT_KEY)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def workflow_status() -> dict[str, Any]:
    """workflow_status。
    :return: 返回处理结果。
    """
    wf = load_monetize_workflow()
    snap = load_monetize_snapshot()
    return {
        "workflow_version": wf.get("version"),
        "title": wf.get("title"),
        "rounds_defined": len(wf.get("research_rounds") or []),
        "pipeline_stages": wf.get("pipeline_stages"),
        "reference_archetypes": wf.get("reference_archetypes"),
        "latest": snap,
    }


def _executive_summary(rounds: list[dict], blueprint: dict[str, Any]) -> str:
    """_executive_summary。

    参数说明：
    :param rounds: 参数 rounds
    :param blueprint: 参数 blueprint
    :return: 返回处理结果。
    """
    lines = ["## Hermes 营销 × AnySearch · 数字产品/智能体变现 深度研究\n"]
    dr = blueprint.get("deep_read") or {}
    lines.append(f"**总览**：{dr.get('summary', '')}\n")
    for r in rounds:
        dept = ", ".join(d.get("seat", "") for d in r.get("departments") or [])
        dec = r.get("decomposition") or {}
        models = ", ".join(m.get("label", "") for m in dec.get("models_detected") or []) or "—"
        lines.append(
            f"**R{r['round']} {r['topic_label']}** ({r['lane']}) hits={r.get('anysearch_hits')} "
            f"models=[{models}] ecc={r.get('ecc_verdict')} → {dept}\n"
        )
    lines.append("\n**推荐架构**：")
    for a in blueprint.get("recommended_archetypes") or []:
        lines.append(f"- {a.get('label')}: {a.get('hermes_fit')}")
    return "\n".join(lines)
