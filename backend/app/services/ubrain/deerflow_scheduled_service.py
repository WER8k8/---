"""DeerFlow 定时更新 — 套餐门控入队 + 分 lane 队列消费。"""



from __future__ import annotations



import json

import logging

from datetime import datetime, timezone

from typing import Any



from sqlalchemy.orm import Session



from app.core.cache import redis_client

from app.core.config import settings

from app.services.ubrain.deerflow_job_service import enqueue_job, run_job, run_pending_jobs

from app.services.ubrain.deerflow_sidecar import deerflow_sidecar_status

from app.services.ubrain.deerflow_tenant_quota import (

    increment_monthly_count,

    resolve_eligible_schedule_tenant_ids,

)



logger = logging.getLogger("uj-admin.deerflow_scheduled")



SNAPSHOT_KEY = "deerflow_scheduled_latest"

DEDUPE_PREFIX = "deerflow:scheduled:day:"





def _schedule_message() -> str:
    """_schedule_message。
    :return: 返回处理结果。
    """
    return (

        getattr(settings, "DEERFLOW_SCHEDULE_MESSAGE", "") or ""

    ).strip() or "定时市场研究：建材出口热点、竞品与区域机会（套餐能力）"





def _auto_enqueue_enabled() -> bool:
    """_auto_enqueue_enabled。
    :return: 返回处理结果。
    """
    flag = getattr(settings, "DEERFLOW_SCHEDULE_AUTO_ENQUEUE_ENABLED", None)
    if flag is not None:

        return bool(flag)

    return False





def _already_scheduled_today(tenant_id: str) -> bool:
    """_already_scheduled_today。

    参数说明：
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    if not redis_client:

        return False

    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    return bool(redis_client.get(f"{DEDUPE_PREFIX}{tenant_id}:{day}"))





def _mark_scheduled_today(tenant_id: str) -> None:
    """_mark_scheduled_today。

    参数说明：
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    if not redis_client:

        return

    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    redis_client.set(f"{DEDUPE_PREFIX}{tenant_id}:{day}", "1", ex=86400 * 2)





def run_deerflow_pending_only(

    db: Session,

    *,

    trigger: str = "scheduler",

    limit: int | None = None,

    tenant_id: str | None = None,

    lane: str = "tenant",

) -> dict[str, Any]:

    """消费 queued 任务；Hermes 运维须 lane=ops。"""
    lim = limit
    if lim is None:

        if lane == "ops":

            lim = int(getattr(settings, "HERMES_OPS_DRAIN_LIMIT", 3) or 3)

        else:

            lim = int(getattr(settings, "DEERFLOW_RUN_PENDING_LIMIT", 10) or 10)

    items = run_pending_jobs(db, tenant_id=tenant_id, limit=lim, lane=lane)
    body = {

        "trigger": trigger,
        "mode": "pending_only",
        "lane": lane,
        "processed": len(items),
        "success": sum(1 for i in items if i.get("status") == "success"),
        "failed": sum(1 for i in items if i.get("status") == "failed"),
        "items": [

            {

                "id": i.get("id"),
                "intent": i.get("intent"),
                "status": i.get("status"),
                "tenant_id": i.get("tenant_id"),

            }
            for i in items

        ],
        "saved_at": datetime.now(timezone.utc).isoformat(),

    }
    _save_snapshot(body)
    return body






def _run_scheduled_auto_enqueue(db, trigger, force, enqueued, skipped, errors):
    """_run_scheduled_auto_enqueue。

    参数说明：
    :param db: 参数 db
    :param trigger: 参数 trigger
    :param force: 参数 force
    :param enqueued: 参数 enqueued
    :param skipped: 参数 skipped
    :param errors: 参数 errors
    :return: 返回处理结果。
    """
    eligible_ids: list[str] = []
    if _auto_enqueue_enabled() or force:

        eligible_ids, gate_skipped = resolve_eligible_schedule_tenant_ids(db, force=force)
        skipped.extend(gate_skipped)
        message = _schedule_message()
        for tid in eligible_ids:

            if not force and _already_scheduled_today(tid):

                skipped.append({"tenant_id": tid, "eligible": True, "reason": "already_scheduled_today"})
                continue

            try:

                job = enqueue_job(

                    db,
                    tenant_id=tid,
                    intent="market_research",
                    payload={

                        "message": message,
                        "context": {"scheduled": True, "trigger": trigger},

                    },
                    created_by=None,

                )
                ran = run_job(db, job.id)
                enqueued.append(

                    {

                        "tenant_id": tid,
                        "job_id": job.id,
                        "status": ran.get("status"),
                        "intent": ran.get("intent"),

                    }

                )
                if ran.get("status") == "success":

                    _mark_scheduled_today(tid)
                    increment_monthly_count(tid)

                elif ran.get("status") == "failed":

                    errors.append(f"{tid[:8]}:{ran.get('error_message') or 'failed'}")

            except Exception as exc:

                logger.warning("DeerFlow scheduled tenant %s failed: %s", tid[:8], exc)
                errors.append(f"{tid[:8]}:{exc}")
    return eligible_ids
def run_scheduled_deerflow_update(

    db: Session,

    *,

    trigger: str = "scheduler",

    force: bool = False,

) -> dict[str, Any]:

    """

    每日槽位：

    - 可选：对套餐合格租户入队 market_research（DEERFLOW_SCHEDULE_AUTO_ENQUEUE_ENABLED）

    - 始终：tenant lane drain（worker 主通道）

    Hermes 不应调用本函数做 15 分钟轮询。

    """
    sidecar = deerflow_sidecar_status()
    enqueued: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[str] = []
    eligible_ids = _run_scheduled_auto_enqueue(db, trigger, force, enqueued, skipped, errors)
    pending = run_deerflow_pending_only(db, trigger=f"{trigger}:tenant_drain", lane="tenant")
    body: dict[str, Any] = {

        "trigger": trigger,
        "mode": "scheduled_batch",
        "auto_enqueue": _auto_enqueue_enabled() or force,
        "eligible_count": len(eligible_ids),
        "enqueued_count": len(enqueued),
        "skipped": skipped[:30],
        "skipped_count": len(skipped),
        "sidecar": {

            "configured": sidecar.get("configured"),
            "healthy": sidecar.get("healthy"),
            "fallback": sidecar.get("fallback"),

        },
        "enqueued": enqueued,
        "tenant_drain": pending,
        "errors": errors[:10],
        "saved_at": datetime.now(timezone.utc).isoformat(),

    }
    _save_snapshot(body)
    if errors:

        _notify_deerflow_failures(body)



    logger.info(

        "DeerFlow scheduled [%s] auto=%s enqueued=%s drain=%s errors=%s",
        trigger,
        body["auto_enqueue"],
        len(enqueued),
        pending.get("processed"),
        len(errors),

    )
    return body





def load_deerflow_schedule_snapshot() -> dict[str, Any] | None:
    """load_deerflow_schedule_snapshot。
    :return: 返回处理结果。
    """
    from app.core.cache import redis_available
    if not redis_available():

        return None

    try:
        raw = redis_client.get(SNAPSHOT_KEY)
    except Exception as exc:
        logger.warning("load_deerflow_schedule_snapshot redis get failed: %s", exc)
        return None

    if not raw:

        return None

    try:

        return json.loads(raw)

    except (json.JSONDecodeError, TypeError):

        return None





def _save_snapshot(body: dict[str, Any]) -> None:
    """_save_snapshot。

    参数说明：
    :param body: 参数 body
    :return: 返回处理结果。
    """
    if not redis_client:

        return

    redis_client.set(SNAPSHOT_KEY, json.dumps(body, ensure_ascii=False), ex=86400 * 14)





def _notify_deerflow_failures(report: dict[str, Any]) -> dict[str, Any]:
    """_notify_deerflow_failures。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    try:

        from app.services.hermes.alert_dispatcher import dispatch_ops_alert
        lines = [

            f"**模式**: {report.get('mode')}",
            f"**自动入队**: {report.get('auto_enqueue')}",
            f"**入队**: {report.get('enqueued_count')} · 跳过 {report.get('skipped_count')}",
            "",
            "**失败**:",

        ]
        for err in report.get("errors") or []:

            lines.append(f"- {err}")

        lines.append("\n指令: `rerun_deerflow` / `deerflow_pending`（Admin → Hermes 运维）")
        return dispatch_ops_alert(

            title="📊 市场研究定时任务 · 部分失败",
            body_md="\n".join(lines),
            template="orange",
            event_type="deerflow_scheduled",
            fingerprint=f"deerflow:{len(report.get('errors') or [])}:{report.get('saved_at', '')[:10]}",

        )

    except Exception as exc:

        logger.info("DeerFlow alert skipped: %s", exc)
        return {"sent": False, "reason": str(exc)}





def resolve_schedule_tenant_ids(db: Session) -> list[str]:
    """resolve_schedule_tenant_ids。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    ids, _ = resolve_eligible_schedule_tenant_ids(db, force=False)
    return ids

