"""DeerFlow 任务队列：入队、执行、轮询（Phase 1 进程内执行，可接 cron）。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.deerflow_job import DeerflowJob
from app.services.ubrain.content_draft_service import write_lead_content_drafts


def _bridge(db: Session):
    """影子双写桥（轮24-A）：TASK_CONTROL_ENABLED 关时完全旁路，桥内自吞异常。"""
    from app.services.tasks.deerflow_bridge import DeerflowTaskBridge
    return DeerflowTaskBridge(db)


def _append_log(job: DeerflowJob, line: str) -> None:
    """_append_log。

    参数说明：
    :param job: 参数 job
    :param line: 参数 line
    :return: 返回处理结果。
    """
    prev = job.log_text or ""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    job.log_text = (prev + f"\n[{ts}] {line}").strip()


def serialize_job(job: DeerflowJob) -> dict[str, Any]:
    """serialize_job。

    参数说明：
    :param job: 参数 job
    :return: 返回处理结果。
    """
    result = None
    if job.result_json:
        try:
            result = json.loads(job.result_json)
        except json.JSONDecodeError:
            result = {"raw": job.result_json}
    payload = {}
    try:
        payload = json.loads(job.payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    return {
        "id": job.id,
        "tenant_id": job.tenant_id,
        "intent": job.intent,
        "status": job.status,
        "payload": payload,
        "result": result,
        "error_message": job.error_message,
        "log_text": job.log_text,
        "created_by": job.created_by,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


def _derive_job_steps(job: DeerflowJob) -> list[dict[str, Any]]:
    """_derive_job_steps。

    参数说明：
    :param job: 参数 job
    :return: 返回处理结果。
    """
    steps: list[dict[str, Any]] = []
    result: dict[str, Any] = {}
    if job.result_json:
        try:
            result = json.loads(job.result_json)
        except json.JSONDecodeError:
            result = {}

    if isinstance(result.get("steps"), list):
        for i, s in enumerate(result["steps"][:12]):
            if isinstance(s, dict):
                steps.append(
                    {
                        "index": i + 1,
                        "title": s.get("title") or s.get("name") or f"步骤 {i + 1}",
                        "status": s.get("status") or job.status,
                    }
                )
            else:
                steps.append({"index": i + 1, "title": str(s), "status": job.status})

    for action in (result.get("accio_actions") or result.get("next_actions") or [])[:8]:
        if isinstance(action, dict):
            steps.append(
                {
                    "index": len(steps) + 1,
                    "title": action.get("skill_id") or action.get("message") or "编排动作",
                    "status": "pending" if action.get("requires_confirmation") else "done",
                }
            )

    wf = result.get("workflow") or (result.get("preflight") or {}).get("workflow")
    if wf and not steps:
        steps.append({"index": 1, "title": str(wf), "status": job.status})

    if not steps and job.log_text:
        for line in (job.log_text or "").splitlines()[-8:]:
            t = line.strip()
            if t:
                steps.append({"index": len(steps) + 1, "title": t[:120], "status": job.status})
    return steps


def serialize_job_with_steps(job: DeerflowJob) -> dict[str, Any]:
    """serialize_job_with_steps。

    参数说明：
    :param job: 参数 job
    :return: 返回处理结果。
    """
    data = serialize_job(job)
    data["steps"] = _derive_job_steps(job)
    if data.get("log_text"):
        lines = [ln for ln in data["log_text"].splitlines() if ln.strip()]
        data["log_tail"] = "\n".join(lines[-6:])
    return data


def enqueue_job(
    db: Session,
    *,
    tenant_id: str,
    intent: str,
    payload: dict[str, Any],
    created_by: str | None = None,
) -> DeerflowJob:
    """enqueue_job。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param intent: 参数 intent
    :param payload: 参数 payload
    :param created_by: 参数 created_by
    :return: 返回处理结果。
    """
    job = DeerflowJob(
        tenant_id=tenant_id,
        intent=intent,
        status="queued",
        payload_json=json.dumps(payload, ensure_ascii=False),
        created_by=created_by,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    _append_log(job, f"queued intent={intent}")
    db.commit()
    _bridge(db).on_job_enqueued(job)
    return job


def _run_lead_content_pack(db: Session, job: DeerflowJob, payload: dict[str, Any]) -> dict[str, Any]:
    """_run_lead_content_pack。

    参数说明：
    :param db: 参数 db
    :param job: 参数 job
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    from app.services.ubrain.orchestrator import UBrainOrchestrator
    message = str(payload.get("message") or "")
    ctx = payload.get("context") or {}
    tenant_id = str(job.tenant_id) if job.tenant_id else None
    if tenant_id:
        from app.services.tenant_product_profile_service import require_product_profile_for_content
        require_product_profile_for_content(db, tenant_id)
    pack = UBrainOrchestrator()._lead_content_pack(
        message,
        ctx,
        db=db,
        tenant_id=tenant_id,
    )
    drafts = write_lead_content_drafts(
        db,
        tenant_id=str(job.tenant_id),
        pack=pack,
        created_by=job.created_by,
    )
    pack["drafts"] = drafts
    pack["cms_draft_count"] = len(drafts)
    return pack


def _run_geo_submit_pack(db: Session, job: DeerflowJob, payload: dict[str, Any]) -> dict[str, Any]:
    """_run_geo_submit_pack。

    参数说明：
    :param db: 参数 db
    :param job: 参数 job
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    from app.services.ubrain.orchestrator import UBrainOrchestrator
    ctx = payload.get("context") or {}
    pack = UBrainOrchestrator()._geo_submit_pack(ctx)
    pack["human_review_required"] = True
    return pack


def _run_matrix_publish(db: Session, job: DeerflowJob, payload: dict[str, Any]) -> dict[str, Any]:
    """_run_matrix_publish。

    参数说明：
    :param db: 参数 db
    :param job: 参数 job
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    from app.services.ubrain.matrix_publish_service import execute_matrix_publish
    message = str(payload.get("message") or "")
    ctx = dict(payload.get("context") or {})
    return execute_matrix_publish(
        db,
        tenant_id=str(job.tenant_id),
        message=message,
        context=ctx,
        user_id=str(job.created_by) if job.created_by else None,
    )


def _dispatch_intent(db: Session, job: DeerflowJob, payload: dict[str, Any]) -> dict[str, Any]:
    """按 job.intent 分发执行具体业务，返回结果 dict；不支持的 intent 抛 ValueError。

    参数说明：
    :param db: 参数 db
    :param job: 参数 job
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    if job.intent == "lead_content_pack":
        result = _run_lead_content_pack(db, job, payload)
    elif job.intent == "find_buyers":
        from app.services.ubrain.accio_sales_service import find_buyer_prospects
        message = str(payload.get("message") or "")
        ctx = payload.get("context") or {}
        result = find_buyer_prospects(
            db,
            tenant_id=str(job.tenant_id),
            message=message,
        )
    elif job.intent == "outreach_letter_pack":
        from app.services.ubrain.accio_sales_service import outreach_letter_pack
        result = outreach_letter_pack(
            db,
            tenant_id=str(job.tenant_id),
            message=str(payload.get("message") or ""),
        )
    elif job.intent == "market_research":
        from app.services.ubrain.commercial_os_bridge import run_market_research
        result = run_market_research(
            db,
            tenant_id=str(job.tenant_id),
            message=str(payload.get("message") or "蓝海市场研究"),
        )
    elif job.intent == "flywheel_loop":
        from app.services.hermes.flywheel_workflow import run_closed_loop_flywheel
        result = run_closed_loop_flywheel(
            db,
            tenant_id=str(job.tenant_id),
            message=str(payload.get("message") or "跑一轮卖货飞轮"),
            user_id=str(job.created_by) if job.created_by else None,
            auto_run_jobs=True,
        )
    elif job.intent == "geo_submit_pack":
        result = _run_geo_submit_pack(db, job, payload)
    elif job.intent == "geo_content_matrix":
        from app.services.tenant_product_profile_service import require_product_profile_for_content
        require_product_profile_for_content(db, str(job.tenant_id))
        from app.services.hermes.agency.orchestrator_bridge import (
            run_geo_matrix_via_agency_sync,
        )
        result = run_geo_matrix_via_agency_sync(
            db,
            tenant_id=str(job.tenant_id),
            message=str(payload.get("message") or ""),
            context=payload.get("context") or {},
            created_by=str(job.created_by) if job.created_by else None,
        )
    elif job.intent == "matrix_publish":
        result = _run_matrix_publish(db, job, payload)
    elif job.intent == "osint_check":
        from app.services.foreign_trade.foreign_trade_agent_service import (
            extract_osint_target,
            run_osint_agent,
        )
        target = str(payload.get("target") or "") or extract_osint_target(
            str(payload.get("message") or ""), payload.get("context") or {}
        )
        if not target:
            raise ValueError("osint_target_required")
        result = run_osint_agent(target)
    elif job.intent == "website_icp":
        from app.services.foreign_trade.foreign_trade_agent_service import run_website_icp_agent
        result = run_website_icp_agent(
            db,
            str(job.tenant_id),
            message=str(payload.get("message") or ""),
            ctx=payload.get("context") or {},
        )
    else:
        raise ValueError(f"unsupported_intent:{job.intent}")
    return result


def run_job(db: Session, job_id: str) -> dict[str, Any]:
    """run_job。

    参数说明：
    :param db: 参数 db
    :param job_id: 参数 job_id
    :return: 返回处理结果。
    """
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        raise ValueError("job_not_found")
    if job.status in ("success", "failed"):
        return serialize_job(job)

    now = datetime.now(timezone.utc)
    job.status = "running"
    job.started_at = now
    job.error_message = None
    _append_log(job, "running")
    db.commit()
    _bridge(db).on_job_started(job)
    try:
        payload = json.loads(job.payload_json or "{}")
        result = _dispatch_intent(db, job, payload)
        job.status = "success"
        job.result_json = json.dumps(result, ensure_ascii=False)
        job.finished_at = datetime.now(timezone.utc)
        _append_log(job, f"success cms_draft_count={result.get('cms_draft_count', 0)}")
        from app.services.ubrain.commercial_os_bridge import on_deerflow_job_finished
        hook = on_deerflow_job_finished(
            db,
            job_id=job.id,
            tenant_id=str(job.tenant_id),
            intent=job.intent,
            status="success",
            result=result,
        )
        result["commercial_os_hook"] = hook
        job.result_json = json.dumps(result, ensure_ascii=False)
        _append_log(job, f"flywheel insight={hook.get('insight_id', '')[:8]}")
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)[:1000]
        job.finished_at = datetime.now(timezone.utc)
        _append_log(job, f"failed: {exc}")

    db.commit()
    db.refresh(job)
    _bridge(db).on_job_finished(job, success=(job.status == "success"))
    _audit_job_finish(db, job)
    # 轮25-B：发布类 intent 终态后旁路留证（best-effort，绝不阻断主链路）
    if job.intent in ("matrix_publish", "geo_submit_pack"):
        _browser_evidence_after_finish(db, job)
    return serialize_job(job)


def _browser_evidence_after_finish(db: Session, job) -> None:
    """发布类 DeerFlow 任务终态后调 Browser Runtime 留证（screenshot 意图）。

    约束：
    - 旁路，不参与 db.commit / db.rollback 主链路（runtime 内部已自吞异常）；
    - 仅当 payload.context.target_url 存在时调用（无 URL = 无留证对象）；
    - 任何异常吞掉——审计 hook 已留痕，browser 失败不阻断 DeerFlow 返回。
    """
    try:
        target_url = None
        try:
            payload = json.loads(job.payload_json or "{}")
            ctx = payload.get("context") or {}
            target_url = ctx.get("target_url") or ctx.get("post_url")
        except (json.JSONDecodeError, TypeError):
            target_url = None
        if not target_url:
            return
        # 异步调 runtime.execute（25-B 是同步骨架调用，asyncio 兜底）
        import asyncio
        from app.services.browser_runtime.runtime import execute as _br_execute

        coro = _br_execute(
            tenant_id=str(job.tenant_id) if job.tenant_id else "",
            actor=f"deerflow:{job.intent}",
            action="screenshot",
            url=target_url,
            metadata={"job_id": str(job.id), "intent": job.intent},
        )
        try:
            asyncio.run(coro)
        except RuntimeError:
            # 已有事件循环（嵌入式运行），降级为同线程调度
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 极端情况：fire-and-forget（25-C 起改为真异步管线）
                    return
                loop.run_until_complete(coro)
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001 — 旁路绝不外泄
        pass


def _audit_job_finish(db: Session, job: DeerflowJob) -> None:
    """A5：DeerFlow 任务完成写入审计（成功/失败均记录）。"""
    try:
        from app.services.ubrain.action_audit_service import log_flywheel_action
        meta: dict[str, Any] = {"job_id": str(job.id), "status": job.status}
        if job.result_json:
            try:
                parsed = json.loads(job.result_json)
                hook = parsed.get("commercial_os_hook") or {}
                if hook.get("insight_id"):
                    meta["insight_id"] = hook["insight_id"]
                pipe = hook.get("pipeline") or {}
                if pipe.get("status"):
                    meta["pipeline_status"] = pipe["status"]
            except json.JSONDecodeError:
                pass
        if job.error_message:
            meta["error"] = job.error_message[:200]
        log_flywheel_action(
            db,
            tenant_id=str(job.tenant_id),
            user_id=str(job.created_by) if job.created_by else None,
            action_type="deerflow_job",
            intent=job.intent,
            message=str((json.loads(job.payload_json or "{}")).get("message") or job.intent)[:280],
            outcome=job.status,
            meta=meta,
        )
    except Exception:
        pass


def _payload_dict(job: DeerflowJob) -> dict[str, Any]:
    """_payload_dict。

    参数说明：
    :param job: 参数 job
    :return: 返回处理结果。
    """
    try:
        return json.loads(job.payload_json or "{}")
    except json.JSONDecodeError:
        return {}


def _job_priority(job: DeerflowJob) -> int:
    """0=用户触发优先，1=Hermes/飞轮，2=平台定时批。"""
    payload = _payload_dict(job)
    ctx = payload.get("context") or {}
    if ctx.get("scheduled"):
        return 2
    if ctx.get("hermes"):
        return 1
    return 0


def run_pending_jobs(
    db: Session,
    *,
    tenant_id: str | None = None,
    limit: int = 10,
    lane: str = "tenant",
) -> list[dict[str, Any]]:
    """
    消费 queued 任务。
    lane=tenant：客户/worker 主通道，按用户优先排序。
    lane=ops：Hermes 运维 drain，限量且不抢占大配额。
    """
    from app.core.config import settings
    lim = int(limit or 10)
    if lane == "ops":
        lim = min(lim, int(getattr(settings, "HERMES_OPS_DRAIN_LIMIT", 3) or 3))

    q = db.query(DeerflowJob).filter(DeerflowJob.status == "queued")
    if tenant_id:
        q = q.filter(DeerflowJob.tenant_id == tenant_id)
    jobs = q.order_by(DeerflowJob.created_at.asc()).limit(max(lim * 3, 20)).all()
    jobs.sort(key=lambda j: (_job_priority(j), j.created_at or datetime.now(timezone.utc)))
    out: list[dict[str, Any]] = []
    for job in jobs[:lim]:
        out.append(run_job(db, job.id))
    return out


def list_jobs(
    db: Session,
    *,
    tenant_id: str,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """list_jobs。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param page: 参数 page
    :param page_size: 参数 page_size
    :return: 返回处理结果。
    """
    q = db.query(DeerflowJob).filter(DeerflowJob.tenant_id == tenant_id)
    total = q.count()
    rows = (
        q.order_by(DeerflowJob.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [serialize_job_with_steps(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
