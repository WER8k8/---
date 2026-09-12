"""DeerFlow 风格深度研究 — Planner / Researcher / Reviewer / Writer → Research Brief。"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.ubrain_commercial_os import UbrainResearchInsight
from app.services.trade_intel_service import blue_ocean, export_feasibility
from app.services.ubrain.tenant_memory_service import get_memory


def _retrieve_prior_insights(
    db: Session, tenant_id: str, *, category: str, limit: int = 5
) -> list[dict[str, Any]]:
    """_retrieve_prior_insights。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param category: 参数 category
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    rows = (
        db.query(UbrainResearchInsight)
        .filter(UbrainResearchInsight.tenant_id == tenant_id)
        .order_by(UbrainResearchInsight.created_at.desc())
        .limit(20)
        .all()
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        if category and category not in (row.summary or ""):
            cats = []
            try:
                import json
                cats = json.loads(row.categories_json or "[]")
            except json.JSONDecodeError:
                pass
            if not any(category in c for c in cats):
                continue
        out.append({"id": row.id, "title": row.title, "summary": (row.summary or "")[:400]})
        if len(out) >= limit:
            break
    return out

_BRIEF_VERSION = "2.0"

_CC_REGION = {
    "SA": "中东",
    "AE": "中东",
    "QA": "中东",
    "VN": "东南亚",
    "TH": "东南亚",
    "MY": "东南亚",
    "ID": "东南亚",
}


def _planner_subtasks(message: str, category: str) -> list[dict[str, str]]:
    """动态任务编排（LangGraph 规划器轻量等价）。"""
    base = [
        {"id": "policy", "name": "出口合规与证照", "agent": "Researcher"},
        {"id": "market", "name": "蓝海市场与需求", "agent": "Researcher"},
        {"id": "competitor", "name": "竞品与差异化卖点", "agent": "Researcher"},
    ]
    if re.search(r"储能|电池|新能源", message):
        base.insert(0, {"id": "tech", "name": "技术路线与标准", "agent": "Researcher"})
    if re.search(r"供应链|物流|海关", message):
        base.append({"id": "supply", "name": "供应链与物流", "agent": "Researcher"})
    if "保温" in message or "建材" in category:
        base.append({"id": "spec", "name": "规格参数与防火等级", "agent": "Researcher"})
    return base


def _researcher_gather(message: str, category: str) -> dict[str, Any]:
    """_researcher_gather。

    参数说明：
    :param message: 参数 message
    :param category: 参数 category
    :return: 返回处理结果。
    """
    bo = blue_ocean(f"{category}蓝海市场")
    recs = bo.get("recommendations") or []
    findings: list[dict[str, Any]] = []
    for r in recs[:5]:
        cc = r.get("country_code") or ""
        findings.append(
            {
                "claim": f"{category} 在 {cc}：{r.get('reason', '')[:120]}",
                "source": "trade_intel/blue_ocean",
                "source_type": "internal_m0",
                "confidence": 0.75 if r.get("competition") != "high" else 0.55,
                "url": None,
                "country_code": cc,
            }
        )
    if recs:
        top_cc = recs[0].get("country_code") or "SA"
        probe = f"{category}能出口{top_cc}吗"
        if "出口" not in message:
            probe = f"{category}出口到{top_cc}"
        fr = export_feasibility(probe)
        findings.append(
            {
                "claim": (
                    f"{fr.category}→{fr.country_code} {fr.verdict_label}；"
                    f"HS第{fr.hs_chapter}章；{fr.summary[:100]}"
                ),
                "source": "trade_intel/export_feasibility",
                "source_type": "internal_m0",
                "confidence": 0.85 if fr.verdict == "go" else 0.6,
                "url": None,
                "country_code": fr.country_code,
            }
        )
    return {
        "recommendations": recs,
        "findings": findings,
        "category": category,
    }


def _reviewer_pass(findings: list[dict[str, Any]], hints: list[str]) -> dict[str, Any]:
    """_reviewer_pass。

    参数说明：
    :param findings: 参数 findings
    :param hints: 参数 hints
    :return: 返回处理结果。
    """
    issues: list[str] = []
    controversies: list[dict[str, str]] = []
    confidences = [f.get("confidence", 0.5) for f in findings]
    if not findings:
        issues.append("Researcher 未产出可验证结论，需补充检索或缩小品类。")
    if confidences and min(confidences) < 0.5:
        issues.append("部分结论置信度偏低，执行前建议人工复核。")
    low = [f for f in findings if (f.get("confidence") or 0) < 0.6]
    high = [f for f in findings if (f.get("confidence") or 0) >= 0.75]
    if low and high:
        controversies.append(
            {
                "topic": "市场机会判断",
                "low_confidence": low[0].get("claim", "")[:80],
                "high_confidence": high[0].get("claim", "")[:80],
            }
        )
    for h in hints[:2]:
        issues.append(f"反馈回流提示：{h}")
    approved = len(issues) <= 2
    return {
        "approved": approved,
        "issues": issues,
        "controversies": controversies,
        "reviewer_agent": "Reviewer",
    }


def _writer_brief(
    *,
    message: str,
    category: str,
    research: dict[str, Any],
    review: dict[str, Any],
    prior_count: int,
) -> dict[str, Any]:
    """_writer_brief。

    参数说明：
    :param message: 参数 message
    :param category: 参数 category
    :param research: 参数 research
    :param review: 参数 review
    :param prior_count: 参数 prior_count
    :return: 返回处理结果。
    """
    recs = research.get("recommendations") or []
    top = recs[0] if recs else {}
    cc = top.get("country_code") or "SA"
    region = _CC_REGION.get(cc, "中东")
    executive = (
        f"针对「{message[:60]}」，{category} 优先关注 {region}（{cc}）。"
        f"已综合 {prior_count} 条历史洞察与 {len(research.get('findings') or [])} 条新发现。"
    )
    if not review.get("approved"):
        executive += " 审核标注需人工确认后再批量找客或发开发信。"

    accio_actions = [
        {
            "skill_id": "find_buyers",
            "skill_label": "自动找客",
            "priority": 1,
            "params": {"message": f"找{region} 8 家{category}采购商"},
            "requires_confirmation": False,
        },
        {
            "skill_id": "outreach_letter_pack",
            "skill_label": "开发信",
            "priority": 2,
            "params": {"message": "生成 5 封双语开发信"},
            "requires_confirmation": True,
        },
        {
            "skill_id": "lead_content_pack",
            "skill_label": "获客内容包",
            "priority": 3,
            "params": {"message": f"今晚生成 8 篇{category}长尾 FAQ"},
            "requires_confirmation": True,
        },
        {
            "skill_id": "geo_submit_pack",
            "skill_label": "GEO 清单",
            "priority": 4,
            "params": {"message": "按 GEO 清单检查独立域"},
            "requires_confirmation": False,
        },
    ]
    return {
        "executive_summary": executive,
        "accio_actions": accio_actions,
        "primary_region": region,
        "primary_country_code": cc,
    }


def build_research_brief(
    db: Session,
    *,
    tenant_id: str,
    message: str,
    template_id: str | None = None,
) -> dict[str, Any]:
    """
    产出标准化 Research Brief（JSON），供 Accio 编排与 n8n 消费。
    对标 DeerFlow 多 Agent；数据源为本系统 trade_intel + 记忆（非全网爬取）。
    """
    mem = get_memory(db, tenant_id)
    category = mem.get("product_category") or "建材"
    if "保温" in message:
        category = "保温建材"
    prior = _retrieve_prior_insights(db, tenant_id, category=category, limit=5)
    hints = mem.get("research_hints") or []
    planner_out = {
        "subtasks": _planner_subtasks(message, category),
        "estimated_parallel": 2,
    }
    researcher_out = _researcher_gather(message, category)
    reviewer_out = _reviewer_pass(researcher_out.get("findings") or [], hints)
    writer_out = _writer_brief(
        message=message,
        category=category,
        research=researcher_out,
        review=reviewer_out,
        prior_count=len(prior),
    )
    brief = {
        "version": _BRIEF_VERSION,
        "brief_id": str(uuid.uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query": message,
        "category": category,
        "framework": "deerflow_lite",
        "agents": {
            "planner": planner_out,
            "researcher": {
                "findings_count": len(researcher_out.get("findings") or []),
                "recommendations": researcher_out.get("recommendations"),
            },
            "reviewer": reviewer_out,
            "writer": writer_out,
        },
        "findings": researcher_out.get("findings") or [],
        "controversies": reviewer_out.get("controversies") or [],
        "executive_summary": writer_out.get("executive_summary"),
        "accio_actions": writer_out.get("accio_actions") or [],
        "prior_insights_used": len(prior),
        "feedback_hints_applied": hints,
        "human_in_the_loop": {
            "checkpoint_recommended": not reviewer_out.get("approved"),
            "questions": reviewer_out.get("issues")[:3],
        },
        "disclaimer": (
            "本简报基于优丁出海参谋 M0 与租户记忆，非阿里国际站私有数据；"
            "外发与上架仍需人工确认。"
        ),
    }
    from app.services.ubrain.deerflow_brief_templates_service import (
        apply_brief_template,
        match_brief_template,
    )
    template = match_brief_template(message, template_id=template_id)
    if template:
        brief = apply_brief_template(brief, template)
    return brief


def run_market_research_v2(
    db: Session,
    *,
    tenant_id: str,
    message: str,
    template_id: str | None = None,
) -> dict[str, Any]:
    """DeerFlow market_research 任务统一入口。"""
    from app.services.ubrain.deerflow_sidecar import fetch_sidecar_research
    sidecar = fetch_sidecar_research(tenant_id=tenant_id, message=message)
    if sidecar and (sidecar.get("research_brief") or sidecar.get("accio_actions")):
        sidecar.setdefault("mode", "deerflow_sidecar")
        if not sidecar.get("executive_summary") and sidecar.get("research_brief"):
            rb = sidecar["research_brief"]
            if isinstance(rb, dict):
                sidecar["executive_summary"] = rb.get("executive_summary", "")
                sidecar.setdefault("category", rb.get("category", "建材"))
        return sidecar

    brief = build_research_brief(
        db, tenant_id=tenant_id, message=message, template_id=template_id
    )
    return {
        "mode": "deerflow_research_brief",
        "research_brief": brief,
        "category": brief["category"],
        "recommendations": brief["agents"]["researcher"].get("recommendations") or [],
        "executive_summary": brief["executive_summary"],
        "accio_actions": brief["accio_actions"],
        "findings": brief["findings"],
        "reviewer_approved": brief["agents"]["reviewer"].get("approved"),
        "prior_insights_used": brief["prior_insights_used"],
        "feedback_hints": brief["feedback_hints_applied"],
        "next_pipeline": " → ".join(
            a["skill_id"] for a in brief["accio_actions"][:3]
        ),
    }
