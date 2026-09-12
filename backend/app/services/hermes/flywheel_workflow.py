"""Hermes 卖货飞轮闭环 — 研究 → 找客 → 编排（内部调度，对外脱敏）。"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.services.hermes.brand_guard import sanitize_public_copy, sanitize_public_data
from app.services.ubrain.accio_sales_service import find_buyer_prospects, outreach_letter_pack
from app.services.foreign_trade.foreign_trade_agent_service import enrich_buyers_with_clean_and_osint
from app.services.ubrain.commercial_os_bridge import (
    flywheel_status,
    run_pipeline_after_deerflow,
)
from app.services.ubrain.deerflow_job_service import enqueue_job, run_job
from app.services.ubrain.tenant_memory_service import get_memory

logger = logging.getLogger(__name__)


def _step(label: str, status: str, **extra: Any) -> dict[str, Any]:
    """_step。

    参数说明：
    :param label: 参数 label
    :param status: 参数 status
    :param **extra: 参数 **extra
    :return: 返回处理结果。
    """
    return {"label": label, "status": status, **extra}


def run_closed_loop_flywheel(
    db: Session,
    *,
    tenant_id: str,
    message: str,
    user_id: str | None = None,
    auto_run_jobs: bool = True,
) -> dict[str, Any]:
    """
    同步执行一轮闭环 MVP：
    市场研究 → 找客入库 → pipeline 编排（开发信等）→ 汇总副驾话术。
    """
    mem = get_memory(db, tenant_id)
    steps: list[dict[str, Any]] = []
    errors: list[str] = []
    research, insight_hook, buyers, diligence, research_job_id = _run_flywheel_research_and_buyers(
        db, tenant_id, message, user_id, auto_run_jobs, mem, steps, errors,
    )
    pipeline, letters = _run_flywheel_pipeline_and_letters(
        db, tenant_id, message, auto_run_jobs, steps, errors,
        research, insight_hook, research_job_id, buyers,
    )
    reply = _build_user_reply(
        research=research,
        buyers=buyers,
        pipeline=pipeline,
        letters=letters,
        errors=errors,
        diligence=diligence,
    )
    ticket_id = pipeline.get("pipeline_run_id") or insight_hook.get("insight_id") or ""
    payload = sanitize_public_data(
        {
            "workflow": "closed_loop_v1",
            "ticket_id": ticket_id,
            "steps": steps,
            "research_summary": (research.get("executive_summary") or "")[:500],
            "buyer_count": buyers.get("count", 0),
            "pipeline_status": pipeline.get("status"),
            "letter_pack_count": letters.get("count") if letters else 0,
            "diligence": diligence,
            "needs_confirmation": True,
            "human_review_required": True,
            "errors": errors,
            "reply": reply,
        }
    )
    return payload


def _build_user_reply(
    *,
    research: dict[str, Any],
    buyers: dict[str, Any],
    pipeline: dict[str, Any],
    letters: dict[str, Any],
    errors: list[str],
    diligence: dict[str, Any] | None = None,
) -> str:
    """_build_user_reply。

    参数说明：
    :param research: 参数 research
    :param buyers: 参数 buyers
    :param pipeline: 参数 pipeline
    :param letters: 参数 letters
    :param errors: 参数 errors
    :param diligence: 参数 diligence
    :return: 返回处理结果。
    """
    summary = (research.get("executive_summary") or "").strip()
    if not summary and isinstance(research.get("research_brief"), dict):
        summary = str(research["research_brief"].get("executive_summary") or "")

    lines = ["【卖货飞轮】本轮已跑完，摘要如下："]
    if summary:
        lines.append(f"1. 市场研究：{summary[:280]}{'…' if len(summary) > 280 else ''}")
    else:
        lines.append("1. 市场研究：已完成，详情可在飞轮卡片查看。")

    bc = buyers.get("count", 0)
    region = buyers.get("region") or "目标区域"
    lines.append(f"2. 找客：已在「{region}」写入 {bc} 条采购商画像（需您核实后再联系）。")
    if diligence:
        clean = diligence.get("prospect_clean") or {}
        stats = (clean.get("data") or {}).get("stats") or {}
        if stats.get("total_out") is not None:
            lines.append(f"2b. 清洗：去重后保留 {stats['total_out']} 条候选。")
        osint_samples = diligence.get("osint_samples") or []
        if osint_samples and osint_samples[0].get("summary"):
            lines.append(f"2c. 背调：{osint_samples[0]['summary']}")

    pstatus = pipeline.get("status") or "pending"
    nsteps = len(pipeline.get("steps") or [])
    lines.append(f"3. 编排：状态 {pstatus}，已规划 {nsteps} 个后续动作。")
    if letters.get("count"):
        lines.append(
            f"4. 开发信：已生成 {letters['count']} 份草稿，请在确认框中审核；"
            "系统不会自动发邮件。"
        )

    lines.append(
        "\n下一步建议：先审开发信 → 本机邮箱发送 → 点「同步反馈」把结果写回研究记忆。"
    )
    if errors:
        lines.append(f"\n（部分步骤有告警：{'；'.join(errors[:2])}，可在运维日志查看。）")
    return sanitize_public_copy("\n".join(lines))


def public_flywheel_status(db: Session, tenant_id: str) -> dict[str, Any]:
    """public_flywheel_status。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    raw = flywheel_status(db, tenant_id)
    raw["product"] = "sales_flywheel"
    if "architecture" in raw:
        raw["architecture"] = "记忆（研究沉淀）→ 执行（找客·开发信）→ 反馈（效果回流）"
    return sanitize_public_data(raw)

def _run_flywheel_research_and_buyers(
    db: Session,
    tenant_id: str,
    message: str,
    user_id: str | None,
    auto_run_jobs: bool,
    mem: Any,
    steps: list[dict[str, Any]],
    errors: list[str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], str]:
    """_run_flywheel_research_and_buyers。

    参数说明：
    :return: 返回 (research, insight_hook, buyers, diligence, research_job_id)。
    """
    # ① 市场研究（单任务入口，避免重复调用）
    steps.append(_step("市场研究", "running"))
    research: dict[str, Any] = {}
    insight_hook: dict[str, Any] = {}
    research_job_id = ""
    try:
        job = enqueue_job(
            db,
            tenant_id=tenant_id,
            intent="market_research",
            payload={"message": message, "context": {"hermes": True}},
            created_by=user_id,
        )
        research_job_id = job.id
        if auto_run_jobs:
            ran = run_job(db, job.id)
            if ran.get("status") == "success" and ran.get("result"):
                research = ran["result"]
            else:
                errors.append(f"研究任务:{ran.get('error_message') or ran.get('status')}")
        steps[-1] = _step(
            "市场研究",
            "done" if research else "queued",
            summary=(research.get("executive_summary") or "")[:200],
            job_id=research_job_id,
        )
        if isinstance(research.get("commercial_os_hook"), dict):
            insight_hook = research["commercial_os_hook"]
    except Exception as exc:
        logger.warning("hermes research failed: %s", exc)
        steps[-1] = _step("市场研究", "failed", error=str(exc)[:200])
        errors.append(f"研究:{exc}")

    # ② 找客
    steps.append(_step("找客画像", "running"))
    buyers: dict[str, Any] = {}
    try:
        buyers = find_buyer_prospects(
            db,
            tenant_id=tenant_id,
            message=message or "找8家中东建材采购商",
            memory=mem,
        )
        steps[-1] = _step(
            "找客画像",
            "done",
            count=buyers.get("count", 0),
            region=buyers.get("region"),
        )
    except Exception as exc:
        steps[-1] = _step("找客画像", "failed", error=str(exc)[:200])
        errors.append(f"找客:{exc}")

    # ②b 潜客清洗 + 可选背调（消息含邮箱/域名时）
    diligence: dict[str, Any] = {}
    if buyers.get("count"):
        steps.append(_step("潜客清洗", "running"))
        try:
            diligence = enrich_buyers_with_clean_and_osint(buyers, message=message, osint_limit=1)
            clean = diligence.get("prospect_clean") or {}
            osint_n = len(diligence.get("osint_samples") or [])
            steps[-1] = _step(
                "潜客清洗",
                "done",
                cleaned=(clean.get("data") or {}).get("stats", {}).get("total_out"),
                osint_samples=osint_n,
            )
        except Exception as exc:
            steps[-1] = _step("潜客清洗", "failed", error=str(exc)[:200])
            errors.append(f"清洗:{exc}")
    return research, insight_hook, buyers, diligence, research_job_id


def _run_flywheel_pipeline_and_letters(
    db: Session,
    tenant_id: str,
    message: str,
    auto_run_jobs: bool,
    steps: list[dict[str, Any]],
    errors: list[str],
    research: dict[str, Any],
    insight_hook: dict[str, Any],
    research_job_id: str,
    buyers: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """_run_flywheel_pipeline_and_letters。

    参数说明：
    :return: 返回 (pipeline, letters)。
    """
    # ③ 管线编排（开发信等）
    steps.append(_step("获客编排", "running"))
    pipeline: dict[str, Any] = {}
    try:
        pipeline = run_pipeline_after_deerflow(
            db,
            tenant_id=tenant_id,
            trigger_job_id=research_job_id or insight_hook.get("insight_id") or "",
            intent="market_research",
            result=research if isinstance(research, dict) else {},
            insight_id=insight_hook.get("insight_id"),
            auto_enqueue=auto_run_jobs,
        )
        created = pipeline.get("created_job_ids") or []
        if auto_run_jobs and created:
            for jid in created[:2]:
                try:
                    run_job(db, jid)
                except Exception as exc:
                    errors.append(f"任务{jid[:8]}:{exc}")
        steps[-1] = _step(
            "获客编排",
            pipeline.get("status", "done"),
            step_count=len(pipeline.get("steps") or []),
            jobs=len(created),
        )
    except Exception as exc:
        steps[-1] = _step("获客编排", "failed", error=str(exc)[:200])
        errors.append(f"编排:{exc}")

    # ④ 可选：有候选则生成开发信草稿包（不发送）
    letters: dict[str, Any] = {}
    if buyers.get("count"):
        try:
            letters = outreach_letter_pack(
                db,
                tenant_id=tenant_id,
                message="为刚找到的采购商生成5封双语开发信草稿",
            )
        except Exception as exc:
            errors.append(f"开发信:{exc}")
    return pipeline, letters

