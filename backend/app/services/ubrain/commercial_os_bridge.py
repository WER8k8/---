"""DeerFlow + AccioWork 商业 OS 飞轮 — 记忆 / 编排 / 反馈（可接 Mem0、n8n）。"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.deerflow_job import DeerflowJob
from app.models.ubrain_accio import BuyerProspectLead
from app.models.ubrain_commercial_os import (
    UbrainFeedbackSnapshot,
    UbrainPipelineRun,
    UbrainResearchInsight,
)
from app.services.inquiries_unified_service import InquiriesUnifiedService
from app.services.ubrain.deerflow_job_service import enqueue_job
from app.services.ubrain.flywheel_integrations import flywheel_integrations_status
from app.services.ubrain.tenant_memory_service import get_memory, merge_memory

_OUTBOUND_ENQUEUE_INTENTS = frozenset({"find_buyers", "outreach_letter_pack"})
_OUTBOUND_WEEKLY_AUTO_CAP = 1


def count_auto_outbound_enqueues(db: Session, tenant_id: str, *, days: int = 7) -> int:
    """研究 Brief 自动编排已入队的 outbound 任务数（防 Token 爆）。"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    runs = (
        db.query(UbrainPipelineRun)
        .filter(
            UbrainPipelineRun.tenant_id == tenant_id,
            UbrainPipelineRun.created_at >= since,
        )
        .all()
    )
    all_job_ids = [
        str(jid)
        for run in runs
        for jid in _jload(run.created_job_ids_json, [])
    ]
    job_map = {}
    if all_job_ids:
        job_map = {
            j.id: j
            for j in db.query(DeerflowJob)
            .filter(
                DeerflowJob.id.in_(all_job_ids),
                DeerflowJob.tenant_id == tenant_id,
            )
            .all()
        }
    total = 0
    for jid_str in all_job_ids:
        job = job_map.get(jid_str)
        if job and job.intent in _OUTBOUND_ENQUEUE_INTENTS:
            total += 1
    return total


def _jload(raw: str | None, default: Any) -> Any:
    """_jload。

    参数说明：
    :param raw: 参数 raw
    :param default: 参数 default
    :return: 返回处理结果。
    """
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _jdump(data: Any) -> str:
    """_jdump。

    参数说明：
    :param data: 参数 data
    :return: 返回处理结果。
    """
    return json.dumps(data, ensure_ascii=False)


def _heuristic_quality(result: dict[str, Any], intent: str) -> float:
    """Ragas 轻量替代：结构完整度 + 可执行字段。"""
    score = 0.55
    if intent == "lead_content_pack" and result.get("topics"):
        score += 0.15
        if result.get("cms_draft_count", 0) > 0:
            score += 0.15
    if intent == "geo_content_matrix" and result.get("steps"):
        score += 0.2
        if result.get("cms_draft_count", 0) > 0:
            score += 0.15
        if result.get("variants"):
            score += 0.1
    if intent == "find_buyers" and result.get("prospects"):
        score += 0.2
        if result.get("count", 0) >= 5:
            score += 0.1
    if intent == "market_research" and (
        result.get("research_brief") or result.get("recommendations")
    ):
        score += 0.25
    if result.get("research_brief", {}).get("findings"):
        score += 0.1
    if result.get("human_verify_required") or result.get("human_review_required"):
        score += 0.05
    return min(round(score, 2), 1.0)


def extract_insight_from_deerflow(
    db: Session,
    *,
    tenant_id: str,
    job_id: str,
    intent: str,
    result: dict[str, Any],
) -> UbrainResearchInsight:
    """DeerFlow 任务成功 → 沉淀可检索洞察（记忆断层闭合）。"""
    regions: list[str] = []
    categories: list[str] = []
    entities: list[dict[str, str]] = []
    tags: list[str] = [intent, "deerflow"]
    if intent == "find_buyers":
        title = f"找客：{result.get('region', '')} {result.get('category', '')}"
        summary = (
            f"生成 {result.get('count', 0)} 条采购商画像；"
            f"{result.get('next_step', '')}"
        )
        if result.get("region"):
            regions.append(str(result["region"]))
        if result.get("category"):
            categories.append(str(result["category"]))
        for p in (result.get("prospects") or [])[:5]:
            entities.append(
                {"type": "buyer_archetype", "value": p.get("title", ""), "relation": "candidate"}
            )
    elif intent == "lead_content_pack":
        title = f"内容研究：{result.get('category', '建材')} × {result.get('count', 0)} 篇"
        topics = result.get("topics") or []
        summary = "选题：" + "；".join(str(t)[:40] for t in topics[:5])
        if result.get("category"):
            categories.append(str(result["category"]))
        tags.append("content")
        for t in topics[:8]:
            entities.append({"type": "topic", "value": str(t)[:120], "relation": "faq_seed"})
    elif intent == "market_research":
        brief = result.get("research_brief") or {}
        title = f"市场研究：{result.get('category', '建材')}"
        summary = result.get("executive_summary") or brief.get("executive_summary") or ""
        if not summary:
            recs = result.get("recommendations") or []
            summary = "；".join(
                f"{r.get('country_code')}:{(r.get('reason') or '')[:50]}"
                for r in recs[:5]
            )
        for f in (brief.get("findings") or result.get("findings") or [])[:8]:
            entities.append(
                {
                    "type": "finding",
                    "value": (f.get("claim") or "")[:120],
                    "relation": f.get("source", ""),
                }
            )
            cc = f.get("country_code")
            if cc:
                regions.append(cc)
        categories.append(str(result.get("category") or "建材"))
        tags.extend(["market", "research_brief"])
    else:
        title = f"研究产出：{intent}"
        summary = json.dumps(result, ensure_ascii=False)[:1500]

    row = UbrainResearchInsight(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        source="deerflow",
        source_job_id=job_id,
        intent=intent,
        title=title[:200],
        summary=summary[:4000],
        entities_json=_jdump(entities),
        tags_json=_jdump(tags),
        regions_json=_jdump(list(dict.fromkeys(regions))),
        categories_json=_jdump(list(dict.fromkeys(categories))),
        quality_score=_heuristic_quality(result, intent),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    from app.services.ubrain.flywheel_integrations import sync_insight_to_mem0
    sync_insight_to_mem0(
        tenant_id=tenant_id,
        insight_id=str(row.id),
        intent=intent,
        title=row.title,
        summary=row.summary,
        quality_score=row.quality_score,
    )
    return row


def retrieve_insights_for_accio(
    db: Session,
    tenant_id: str,
    *,
    region: str | None = None,
    category: str | None = None,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Accio 执行前检索历史研究（Mem0 检索等价）。"""
    rows = (
        db.query(UbrainResearchInsight)
        .filter(UbrainResearchInsight.tenant_id == tenant_id)
        .order_by(UbrainResearchInsight.created_at.desc())
        .limit(50)
        .all()
    )
    scored: list[tuple[float, UbrainResearchInsight]] = []
    for row in rows:
        score = float(row.quality_score or 0.5)
        regions = _jload(row.regions_json, [])
        cats = _jload(row.categories_json, [])
        if region and region in regions:
            score += 0.25
        if category and any(category in c or c in category for c in cats):
            score += 0.2
        scored.append((score, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: list[dict[str, Any]] = []
    for _, row in scored[:limit]:
        out.append(
            {
                "id": row.id,
                "title": row.title,
                "summary": row.summary[:400],
                "intent": row.intent,
                "quality_score": row.quality_score,
                "tags": _jload(row.tags_json, []),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )
    return out


def _pipeline_steps_for_intent(intent: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    """研究完成 → 自动生成 Accio 下一步（执行断层闭合）。"""
    actions = result.get("accio_actions")
    if not actions and result.get("research_brief"):
        actions = (result["research_brief"] or {}).get("accio_actions")
    if actions:
        steps: list[dict[str, Any]] = []
        for a in sorted(actions, key=lambda x: x.get("priority", 99)):
            skill = a.get("skill_id")
            if not skill:
                continue
            steps.append(
                {
                    "step": skill,
                    "enqueue_intent": skill,
                    "message": (a.get("params") or {}).get("message", ""),
                    "requires_confirmation": a.get("requires_confirmation", False),
                    "from_research_brief": True,
                }
            )
        return [s for s in steps if s.get("enqueue_intent")]

    if intent == "market_research":
        recs = result.get("recommendations") or []
        cc = recs[0].get("country_code") if recs else "SA"
        region = "中东" if cc in ("SA", "AE", "QA") else "东南亚"
        return [
            {
                "step": "find_buyers",
                "enqueue_intent": "find_buyers",
                "message": f"找{region} 8 家{result.get('category', '建材')}采购商",
            },
            {
                "step": "outreach_letter_pack",
                "enqueue_intent": "outreach_letter_pack",
                "message": "生成 5 封双语开发信",
                "depends_on": "find_buyers",
            },
        ]
    if intent == "find_buyers":
        return [
            {
                "step": "outreach_letter_pack",
                "enqueue_intent": "outreach_letter_pack",
                "message": "生成 5 封双语开发信",
            },
        ]
    if intent == "lead_content_pack":
        return [
            {
                "step": "matrix_publish_hint",
                "enqueue_intent": None,
                "message": "内容包已就绪，请在统一发布母版人审后矩阵分发",
                "manual": True,
            },
        ]
    if intent == "geo_content_matrix":
        return [
            {
                "step": "matrix_publish_hint",
                "enqueue_intent": None,
                "message": "GEO 母版与平台变体已就绪，请在统一发布母版人审后矩阵分发",
                "manual": True,
            },
        ]
    return []


def run_pipeline_after_deerflow(
    db: Session,
    *,
    tenant_id: str,
    trigger_job_id: str,
    intent: str,
    result: dict[str, Any],
    insight_id: str | None = None,
    auto_enqueue: bool = True,
) -> dict[str, Any]:
    """run_pipeline_after_deerflow。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param trigger_job_id: 参数 trigger_job_id
    :param intent: 参数 intent
    :param result: 参数 result
    :param insight_id: 参数 insight_id
    :param auto_enqueue: 参数 auto_enqueue
    :return: 返回处理结果。
    """
    steps = _pipeline_steps_for_intent(intent, result)
    run = UbrainPipelineRun(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        trigger_job_id=trigger_job_id,
        insight_id=insight_id,
        status="running",
        steps_json=_jdump(steps),
    )
    db.add(run)
    db.commit()
    created_jobs: list[str] = []
    errors: list[str] = []
    outbound_slots = max(
        0,
        _OUTBOUND_WEEKLY_AUTO_CAP - count_auto_outbound_enqueues(db, tenant_id),
    )
    for step in steps:
        enq = step.get("enqueue_intent")
        if not enq or not auto_enqueue:
            continue
        if enq in _OUTBOUND_ENQUEUE_INTENTS:
            if outbound_slots <= 0:
                errors.append(f"{enq}:weekly_outbound_cap")
                continue
            outbound_slots -= 1
        try:
            job = enqueue_job(
                db,
                tenant_id=tenant_id,
                intent=enq,
                payload={
                    "message": step.get("message", ""),
                    "context": {
                        "pipeline_run_id": run.id,
                        "from_insight_id": insight_id,
                        "from_job_id": trigger_job_id,
                    },
                },
            )
            created_jobs.append(job.id)
        except Exception as exc:
            errors.append(f"{enq}:{exc}")

    run.created_job_ids_json = _jdump(created_jobs)
    run.status = "success" if not errors else ("partial" if created_jobs else "failed")
    run.error_message = "; ".join(errors)[:1000] if errors else None
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "pipeline_run_id": run.id,
        "status": run.status,
        "steps": steps,
        "created_job_ids": created_jobs,
        "errors": errors,
        "outbound_weekly_cap": _OUTBOUND_WEEKLY_AUTO_CAP,
        "outbound_cap_skipped": [e for e in errors if e.endswith(":weekly_outbound_cap")],
    }


def _gather_prospect_metrics(
    db: Session,
    tenant_id: str,
    since: datetime,
    period_days: int,
) -> tuple[dict[str, Any], list[BuyerProspectLead], list[BuyerProspectLead], list[BuyerProspectLead]]:
    """汇总询盘/找客基础指标，返回（metrics, prospects, sent, draft_ready）。"""
    inq = InquiriesUnifiedService(db).list_page(page=1, page_size=500, tenant_id=tenant_id)
    items = inq.get("items") or []
    with_phone = [
        i
        for i in items
        if re.search(r"1[3-9]\d{9}", str(i.get("phone") or ""))
    ]
    prospects = (
        db.query(BuyerProspectLead)
        .filter(
            BuyerProspectLead.tenant_id == tenant_id,
            BuyerProspectLead.created_at >= since,
        )
        .all()
    )
    sent = [p for p in prospects if p.status == "contact_sent"]
    draft_ready = [p for p in prospects if p.status == "draft_ready"]
    metrics = {
        "period_days": period_days,
        "inquiries_sample": len(items),
        "inquiries_with_phone": len(with_phone),
        "prospects_discovered": len(prospects),
        "prospects_outreach_sent": len(sent),
        "prospects_draft_ready": len(draft_ready),
        "phone_rate": round(len(with_phone) / max(len(items), 1), 3),
        "outreach_send_rate": round(len(sent) / max(len(prospects), 1), 3),
    }
    return metrics, prospects, sent, draft_ready


def _augment_publish_metrics(db: Session, tenant_id: str, metrics: dict[str, Any]) -> None:
    """补充发布/收录/视频矩阵成功指标（失败静默忽略）。"""
    try:
        from app.models.content import InclusionStatus, PublishTask
        from app.models.media_factory import MediaRenderTask
        pub_total = db.query(PublishTask).filter(PublishTask.status == "success").count()
        pub_failed = db.query(PublishTask).filter(PublishTask.status == "failed").count()
        inc_total = db.query(InclusionStatus).count()
        inc_ok = db.query(InclusionStatus).filter(InclusionStatus.is_included.is_(True)).count()
        video_done = (
            db.query(MediaRenderTask)
            .filter(MediaRenderTask.tenant_id == tenant_id, MediaRenderTask.status == "success")
            .count()
        )
        metrics["publish_success"] = pub_total
        metrics["publish_failed"] = pub_failed
        metrics["inclusion_rate"] = round(inc_ok / max(inc_total, 1), 3) if inc_total else None
        metrics["video_matrix_success"] = video_done
    except Exception:
        pass


def _build_feedback_recommendations(
    metrics: dict[str, Any],
    prospects: list[BuyerProspectLead],
    with_phone_count: int,
) -> list[str]:
    """根据指标生成下一轮研究建议。"""
    recommendations: list[str] = []
    if metrics["phone_rate"] < 0.3:
        recommendations.append(
            "独立域表单手机号必填率偏低，下一轮优先研究落地页与 GEO 转化。"
        )
    if len(prospects) > 3 and metrics["outreach_send_rate"] < 0.2:
        recommendations.append(
            "找客多但开发信发送少，建议批量生成开发信并安排跟进日历。"
        )
    if with_phone_count >= 3 and metrics["outreach_send_rate"] >= 0.3:
        recommendations.append(
            "线索与外联表现良好，可加深高转化区域的市场研究。"
        )
    if metrics.get("inclusion_rate") is not None and metrics["inclusion_rate"] < 0.5:
        recommendations.append("矩阵收录率偏低，下一轮研究应聚焦落地页与标题优化。")
    if int(metrics.get("video_matrix_success") or 0) >= 1:
        recommendations.append("视频矩阵已有成功分发，可复盘高播放平台的选题方向。")
    return recommendations


def _persist_feedback_snapshot(
    db: Session,
    tenant_id: str,
    period_days: int,
    metrics: dict[str, Any],
    recommendations: list[str],
) -> UbrainFeedbackSnapshot:
    """保存反馈快照并同步记忆 / PostHog 事件。"""
    snap = UbrainFeedbackSnapshot(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        period_days=period_days,
        metrics_json=_jdump(metrics),
        recommendations_json=_jdump(recommendations),
    )
    db.add(snap)
    db.commit()
    merge_memory(
        db,
        tenant_id,
        {
            "last_feedback": metrics,
            "research_hints": recommendations,
            "tool_stats": {"feedback_sync": 1},
        },
    )
    from app.services.ubrain.flywheel_integrations import capture_posthog_event
    capture_posthog_event(
        event="flywheel_feedback_sync",
        tenant_id=tenant_id,
        properties={"metrics": metrics, "snapshot_id": snap.id},
    )
    return snap


def collect_sales_feedback(db: Session, tenant_id: str, *, period_days: int = 7) -> dict[str, Any]:
    """询盘/找客/发送 → 效果指标（反馈断层闭合，PostHog 等价）。"""
    since = datetime.now(timezone.utc) - timedelta(days=period_days)
    metrics, prospects, sent, draft_ready = _gather_prospect_metrics(db, tenant_id, since, period_days)
    _augment_publish_metrics(db, tenant_id, metrics)
    recommendations = _build_feedback_recommendations(
        metrics,
        prospects,
        with_phone_count=metrics["inquiries_with_phone"],
    )
    snap = _persist_feedback_snapshot(db, tenant_id, period_days, metrics, recommendations)

    assistant_prompt = (
        "上周数据："
        f"带手机号线索 {metrics['inquiries_with_phone']}，"
        f"已发开发信 {metrics['prospects_outreach_sent']}。"
        + (recommendations[0] if recommendations else "维持当前策略。")
    )
    return {
        "snapshot_id": snap.id,
        "metrics": metrics,
        "recommendations": recommendations,
        "assistant_prompt": assistant_prompt,
        "deerflow_next_prompt": assistant_prompt,
    }


def on_deerflow_job_finished(
    db: Session,
    *,
    job_id: str,
    tenant_id: str,
    intent: str,
    status: str,
    result: dict[str, Any] | None,
) -> dict[str, Any]:
    """DeerFlow 任务结束统一钩子。"""
    if status != "success" or not result:
        return {"hook": "skipped", "reason": status}

    insight = extract_insight_from_deerflow(
        db,
        tenant_id=tenant_id,
        job_id=job_id,
        intent=intent,
        result=result,
    )
    pipeline = run_pipeline_after_deerflow(
        db,
        tenant_id=tenant_id,
        trigger_job_id=job_id,
        intent=intent,
        result=result,
        insight_id=insight.id,
        auto_enqueue=os.getenv("UBRAIN_AUTO_PIPELINE", "1") != "0",
    )
    from app.services.ubrain.flywheel_integrations import capture_posthog_event
    capture_posthog_event(
        event="flywheel_deerflow_job_success",
        tenant_id=tenant_id,
        properties={
            "job_id": job_id,
            "intent": intent,
            "insight_id": insight.id,
            "pipeline_status": pipeline.get("status"),
            "quality_score": insight.quality_score,
        },
    )
    from app.services.ubrain.quality_gate_service import maybe_enqueue_quality_rerun
    payload_msg = ""
    job_row = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if job_row:
        pl = _jload(job_row.payload_json, {})
        payload_msg = str(pl.get("message") or "")
    rerun = maybe_enqueue_quality_rerun(
        db,
        tenant_id=tenant_id,
        source_job_id=job_id,
        intent=intent,
        quality_score=insight.quality_score,
        original_message=payload_msg or intent,
    )
    return {
        "insight_id": insight.id,
        "insight_quality": insight.quality_score,
        "pipeline": pipeline,
        "quality_rerun": rerun,
    }


def list_recent_pipelines(
    db: Session,
    tenant_id: str,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """最近 Accio 编排记录（副驾轮询）。"""
    rows = (
        db.query(UbrainPipelineRun)
        .filter(UbrainPipelineRun.tenant_id == tenant_id)
        .order_by(UbrainPipelineRun.created_at.desc())
        .limit(limit)
        .all()
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        steps = _jload(row.steps_json, [])
        job_ids = _jload(row.created_job_ids_json, [])
        out.append(
            {
                "id": row.id,
                "status": row.status,
                "trigger_job_id": row.trigger_job_id,
                "insight_id": row.insight_id,
                "steps": steps,
                "step_count": len(steps),
                "created_job_ids": job_ids,
                "job_count": len(job_ids),
                "error_message": (row.error_message or "")[:200] or None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "finished_at": row.finished_at.isoformat() if row.finished_at else None,
            }
        )
    return out


def flywheel_status(db: Session, tenant_id: str) -> dict[str, Any]:
    """flywheel_status。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    insight_count = (
        db.query(UbrainResearchInsight)
        .filter(UbrainResearchInsight.tenant_id == tenant_id)
        .count()
    )
    pipeline_count = (
        db.query(UbrainPipelineRun)
        .filter(UbrainPipelineRun.tenant_id == tenant_id)
        .count()
    )
    last_feedback = (
        db.query(UbrainFeedbackSnapshot)
        .filter(UbrainFeedbackSnapshot.tenant_id == tenant_id)
        .order_by(UbrainFeedbackSnapshot.created_at.desc())
        .first()
    )
    last_pipeline = (
        db.query(UbrainPipelineRun)
        .filter(UbrainPipelineRun.tenant_id == tenant_id)
        .order_by(UbrainPipelineRun.created_at.desc())
        .first()
    )
    recent_insights = retrieve_insights_for_accio(db, tenant_id, limit=3)
    mem = get_memory(db, tenant_id)
    feedback_metrics = _jload(last_feedback.metrics_json, None) if last_feedback else None
    auto_pipeline = os.getenv("UBRAIN_AUTO_PIPELINE", "1") != "0"
    pipeline_jobs = (
        _jload(last_pipeline.created_job_ids_json, []) if last_pipeline else []
    )
    return {
        "product": "commercial_flywheel_os",
        "company_name": mem.get("company_name") or "",
        "architecture": "记忆（研究沉淀）→ 执行（找客·开发信）→ 反馈（效果回流）",
        "memory_layer": "ubrain_research_insights + ubrain_tenant_memory",
        "external_slots": {
            "mem0": os.getenv("MEM0_API_URL", ""),
            "n8n_webhook": "/api/v1/ubrain/commercial-os/webhook",
            "posthog": os.getenv("POSTHOG_HOST", ""),
        },
        "integrations": flywheel_integrations_status(),
        "auto_pipeline_enabled": auto_pipeline,
        "insight_count": insight_count,
        "pipeline_run_count": pipeline_count,
        "tool_use_count": mem.get("tool_use_count", 0),
        "last_feedback": feedback_metrics,
        "research_hints": mem.get("research_hints") or [],
        "recent_insights": recent_insights,
        "last_pipeline": (
            {
                "id": last_pipeline.id,
                "status": last_pipeline.status,
                "created_job_ids": pipeline_jobs,
                "finished_at": (
                    last_pipeline.finished_at.isoformat()
                    if last_pipeline and last_pipeline.finished_at
                    else None
                ),
            }
            if last_pipeline
            else None
        ),
        "pillars": {
            "memory": {
                "label": "记忆",
                "status": "active" if insight_count else "empty",
                "count": insight_count,
                "hint": "市场研究自动沉淀，执行任务前自动调取记忆",
            },
            "execution": {
                "label": "执行",
                "status": "active" if pipeline_count else "idle",
                "count": pipeline_count,
                "auto_pipeline": auto_pipeline,
                "hint": "研究简报 → 找客/开发信任务队列",
            },
            "feedback": {
                "label": "反馈",
                "status": "active" if last_feedback else "pending",
                "metrics": feedback_metrics,
                "hint": "询盘/外联指标写回 research_hints，驱动下一轮研究",
            },
        },
    }


def run_market_research(
    db: Session,
    *,
    tenant_id: str,
    message: str,
) -> dict[str, Any]:
    """DeerFlow 市场研究 → Research Brief v1（多 Agent 轻量版）。"""
    from app.services.ubrain.deerflow_research_service import run_market_research_v2
    return run_market_research_v2(db, tenant_id=tenant_id, message=message)
