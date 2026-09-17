# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from celery import shared_task
from typing import Any
import asyncio
import logging

from app.services.job_gateway import JobGateway, JobNotFoundError

logger = logging.getLogger(__name__)


def _get_db_and_job(gw: JobGateway, job_id: str) -> tuple[Any, dict[str, Any]]:
    """获取数据库连接和任务信息。"""
    from app.core.database import SessionLocal
    db = SessionLocal()
    job = gw.get(job_id)
    gw.mark(job_id, "running")
    return db, job


def _parse_payload(job: dict[str, Any]) -> dict[str, Any]:
    """解析任务 payload。"""
    import json
    try:
        return json.loads(job.get("payload_json") or "{}")
    except Exception:
        return {}


def _run_ops_hermes_full_cycle(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行 Hermes 全周期。"""
    from app.services.hermes.ops_autopilot import run_full_ops_cycle
    return run_full_ops_cycle(db, trigger=str(payload.get("trigger") or "celery_job"))


def _run_ops_hermes_site_patrol(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行站点巡检。"""
    from app.services.hermes.site_patrol_service import run_site_patrol
    return run_site_patrol(db, trigger=str(payload.get("trigger") or "celery_job"))


def _run_heal_pipeline(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行修复流水线。"""
    from app.services.heal_pipeline import run_heal_pipeline
    heal_id = str(payload.get("heal_id") or "")
    return run_heal_pipeline(db, heal_id)


def _run_deerflow_scheduled(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行 DeerFlow 定时更新。"""
    from app.services.ubrain.deerflow_scheduled_service import run_scheduled_deerflow_update
    return run_scheduled_deerflow_update(
        db, trigger=str(payload.get("trigger") or "celery_job"), force=True
    )


def _run_marketing_monetize(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行营销变现工作流。"""
    from app.services.hermes.marketing_anysearch_workflow_service import run_monetize_workflow
    return run_monetize_workflow(
        db,
        max_rounds=payload.get("max_rounds"),
        trigger=str(payload.get("trigger") or "celery_job"),
    )


def _run_continuous_iteration(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行持续迭代。"""
    from app.services.hermes.hermes_continuous_iteration_service import run_continuous_iteration_cycle
    return run_continuous_iteration_cycle(
        db,
        trigger=str(payload.get("trigger") or "celery_job"),
        force=bool(payload.get("force") or False),
    )


def _run_greedy_agency(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行贪婪代理编排。"""
    from app.services.hermes.greedy_agency_orchestrator_service import run_greedy_orchestration
    return run_greedy_orchestration(
        db,
        workflow_id=payload.get("workflow_id"),
        playbook_id=payload.get("playbook_id"),
        intent=payload.get("intent"),
        inputs=payload.get("inputs") or {},
        max_steps=payload.get("max_steps"),
    )


def _run_ecommerce_spider(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行电商爬虫。"""
    from app.services.crawlers.ecommerce_crawlers_sidecar import run_spider
    from app.services.crawlers.ecommerce_crawlers_smart import enrich_result_zh
    return enrich_result_zh(run_spider(
        str(payload.get("spider_id") or ""),
        params=payload.get("params") or {},
        tenant_id=payload.get("tenant_id"),
        operator_role=payload.get("operator_role"),
        compliance_acknowledged=bool(payload.get("compliance_acknowledged")),
        tenant_consent=bool(payload.get("tenant_consent")),
        purpose=payload.get("purpose"),
    ))


def _run_growth_agent(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行增长代理。"""
    from app.services.agent_loop.growth_workflow import execute_growth_run
    execute_growth_run(db, str(payload["run_id"]), tenant_id=payload.get("tenant_id"))
    return {"run_id": payload.get("run_id"), "dispatched": True}


def _run_egress_provision(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行出口代理配置。"""
    from app.services.egress_jit_provision_service import process_provision_job
    pid = str(payload.get("provision_job_id") or "")
    if not pid:
        raise ValueError("provision_job_id required")
    report = process_provision_job(db, pid)
    if not report.get("ok"):
        raise RuntimeError(
            report.get("error")
            or report.get("reason")
            or "egress provision failed"
        )
    return report


def _run_media_render(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行媒体渲染。"""
    from app.services.media_render_worker import run_render_task_background
    run_render_task_background(str(payload["task_id"]))
    return {"task_id": payload.get("task_id"), "dispatched": True}


def _run_feishu_event(payload: dict[str, Any]) -> dict[str, Any]:
    """运行飞书事件。"""
    from app.services.feishu import message_handler
    body = payload.get("body") or {}
    maybe = message_handler.handle_event(body)
    if asyncio.iscoroutine(maybe):
        asyncio.run(maybe)
    return {"handled": True}


def _run_pipedrive_sync(payload: dict[str, Any]) -> dict[str, Any]:
    """运行 Pipedrive 同步。"""
    from app.core.config import settings as _settings
    from app.services.integration.pipedrive_connector import PipedriveConnector
    lifecycle = payload.get("lifecycle_data") or {}
    connector = PipedriveConnector(
        api_token=getattr(_settings, "PIPEDRIVE_API_TOKEN", ""),
        base_url=getattr(_settings, "PIPEDRIVE_BASE_URL", "https://api.pipedrive.com/v1"),
        enabled=getattr(_settings, "PIPEDRIVE_SYNC_ENABLED", False),
    )
    return connector.sync_customer_lifecycle(lifecycle)


def _run_super_research(payload: dict[str, Any]) -> dict[str, Any]:
    """运行超级研究。"""
    from app.api.v1.routes import super_agent as _sa
    asyncio.run(_sa._run_research_background(
        str(payload["report_id"]),
        str(payload.get("topic") or ""),
        str(payload.get("depth") or "standard"),
        payload.get("focus_areas") or ["market", "competition", "compliance"],
    ))
    return {"report_id": payload.get("report_id"), "dispatched": True}


def _run_super_execution(payload: dict[str, Any]) -> dict[str, Any]:
    """运行超级执行。"""
    from app.api.v1.routes import super_agent as _sa
    asyncio.run(_sa._run_execution_background(
        str(payload["execution_id"]), payload.get("instruction") or {}
    ))
    return {"execution_id": payload.get("execution_id"), "dispatched": True}


def _run_super_workflow(payload: dict[str, Any]) -> dict[str, Any]:
    """运行超级工作流。"""
    from app.api.v1.routes import super_agent as _sa
    asyncio.run(_sa._run_workflow_background(
        str(payload["workflow_id"]),
        str(payload.get("topic") or ""),
        str(payload.get("depth") or "standard"),
        payload.get("target_platforms") or ["shopify", "facebook"],
        str(payload.get("execution_mode") or "semi-auto"),
        payload.get("focus_areas") or ["market", "competition", "compliance"],
    ))
    return {"workflow_id": payload.get("workflow_id"), "dispatched": True}


def _run_talking_stick_scan(payload: dict[str, Any]) -> dict[str, Any]:
    """运行 Talking Stick 扫描。"""
    from app.services.talking_stick.config import ConfigManager
    from app.services.talking_stick.scheduler import Scheduler
    cm = ConfigManager()
    try:
        cm.load()
    except Exception:
        pass
    sched = Scheduler(cm)
    target = str(payload.get("target_url") or payload.get("target_path") or "")
    options = dict(payload.get("options") or {})
    options["scan_type"] = payload.get("scan_type") or options.get("scan_type") or "full"
    async def _run():
        """_run。
        :return: 返回处理结果。
        """
        return await sched._execute_agent_pipeline(target, options)

    report = asyncio.run(_run())
    if not isinstance(report, dict):
        report = {"scan_result": report}
    report["target_url"] = target
    return report


def _run_lead_search(payload: dict[str, Any]) -> dict[str, Any]:
    """运行线索搜索。"""
    from app.services.ubrain.lead_search_task import execute_lead_search
    asyncio.run(
        execute_lead_search(
            task_id=str(payload["task_id"]),
            keywords=payload.get("keywords"),
            country=payload.get("country"),
            industry=payload.get("industry"),
            max_results=payload.get("max_results"),
            verify_emails=payload.get("verify_emails"),
            min_confidence=payload.get("min_confidence"),
        )
    )
    return {"task_id": payload.get("task_id"), "dispatched": True}


def _run_onboarding_autopilot(payload: dict[str, Any]) -> dict[str, Any]:
    """运行入驻自动化。"""
    from app.services.onboarding_autopilot_job import run_onboarding_autopilot_job
    return run_onboarding_autopilot_job(
        tenant_id=str(payload.get("tenant_id") or ""),
        user_id=str(payload.get("user_id") or ""),
        product_name=str(payload.get("product_name") or ""),
    )


def _run_greedy_revenue_loop(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行贪婪收入循环。"""
    from app.services.hermes.greedy_revenue_loop_service import run_greedy_revenue_loop
    return run_greedy_revenue_loop(
        db,
        message=payload.get("message"),
        locale=str(payload.get("locale") or "global"),
        survival_goal_cny=payload.get("survival_goal_cny"),
        max_agency_steps=payload.get("max_agency_steps"),
        trigger=str(payload.get("trigger") or "celery_job"),
    )


def _run_outreach_email_step(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """运行外发邮件步骤。"""
    from app.services.acquisition_outreach_service import send_outreach_step
    outreach_id = str(payload.get("outreach_id") or "")
    if not outreach_id:
        raise ValueError("outreach_id required")
    report = send_outreach_step(db, outreach_id=outreach_id)
    if not report.get("ok") and not report.get("idempotent"):
        raise RuntimeError(
            report.get("error_code")
            or report.get("error")
            or "outreach email step failed"
        )
    return report


# 任务类型处理器映射
JOB_TYPE_HANDLERS = {
    "ops.hermes_full_cycle": _run_ops_hermes_full_cycle,
    "ops.hermes_site_patrol": _run_ops_hermes_site_patrol,
    "heal.run": _run_heal_pipeline,
    "ops.deerflow_scheduled": _run_deerflow_scheduled,
    "ops.marketing_monetize": _run_marketing_monetize,
    "ops.continuous_iteration": _run_continuous_iteration,
    "ops.greedy_agency": _run_greedy_agency,
    "ops.ecommerce_spider": _run_ecommerce_spider,
    "ops.growth_agent": _run_growth_agent,
    "ops.egress_provision": _run_egress_provision,
    "ops.media_render": _run_media_render,
    "ops.feishu_event": _run_feishu_event,
    "ops.pipedrive_sync": _run_pipedrive_sync,
    "ops.super_research": _run_super_research,
    "ops.super_execution": _run_super_execution,
    "ops.super_workflow": _run_super_workflow,
    "ops.talking_stick_scan": _run_talking_stick_scan,
    "ops.lead_search": _run_lead_search,
    "ops.onboarding_autopilot": _run_onboarding_autopilot,
    "ops.greedy_revenue_loop": _run_greedy_revenue_loop,
    "outreach.email_step": _run_outreach_email_step,
}


@shared_task(
    bind=True,
    name="app.tasks.ops_scheduler_tasks.run_platform_job",
    max_retries=3,  # 增加到3次重试，允许更多恢复机会
    default_retry_delay=60,
    countdown=None,  # 使用 Celery 的指数退避
)
def run_platform_job(self, job_id: str):
    """Execute a queued platform_jobs row (C4 / JobGateway enqueue target).

    改进了错误处理：
    - 失败时标记状态并记录详细错误
    - 超过最大重试次数后移至死信队列
    """
    gw = JobGateway(None)  # 将在函数内初始化
    db, job = _get_db_and_job(gw, job_id)
    jt = job["job_type"]
    payload = _parse_payload(job)
    try:
        handler = JOB_TYPE_HANDLERS.get(jt)
        if not handler:
            raise ValueError(f"unsupported_job_type:{jt}")

        if jt in ("ops.hermes_full_cycle", "ops.hermes_site_patrol", "heal.run",
                  "ops.deerflow_scheduled", "ops.marketing_monetize",
                  "ops.continuous_iteration", "ops.greedy_agency",
                  "ops.ecommerce_spider", "ops.egress_provision",
                  "ops.greedy_revenue_loop", "outreach.email_step"):
            report = handler(db, payload)
        else:
            report = handler(payload)

        if not isinstance(report, dict):
            report = {"result": report}
        gw.mark(job_id, "succeeded", result=report)
        return {"job_id": job_id, "status": "succeeded", "report_keys": list(report.keys())[:20]}
    except JobNotFoundError:
        # 任务不存在，直接放弃
        logger.warning("Job not found, abandoning: job_id=%s", job_id)
        gw.mark(job_id, "abandoned", error_code="JOB_NOT_FOUND")
        raise
    except Exception as exc:
        logger.exception("run_platform_job failed job_id=%s attempt=%s", job_id, self.request.retries)
        try:
            JobGateway(db).mark(
                job_id,
                "failed",
                error_code="PLATFORM_JOB_FAILED",
                error_message=str(exc)[:1000],
                retry_count=getattr(self.request, 'retries', 0),
            )
        except Exception:
            logger.exception("mark failed for job_id=%s", job_id)

        # 检查是否还有重试机会
        if self.request.retries >= self.max_retries:
            # 已达到最大重试次数，移至死信队列
            logger.error(
                "Job exhausted retries, moving to dead letter queue: job_id=%s max_retries=%s",
                job_id,
                self.max_retries,
            )
            try:
                JobGateway(db).mark(
                    job_id,
                    "dead_letter",
                    error_code="MAX_RETRIES_EXCEEDED",
                    error_message=f"Exceeded {self.max_retries} retries",
                )
            except Exception:
                logger.exception("mark dead letter for job_id=%s", job_id)
            raise self.retry(exc=exc, max_retries=0) from exc  # 不再重试

        raise self.retry(exc=exc) from exc
    finally:
        db.close()


def _safe_run(name: str, fn):
    """安全执行定时任务，记录详细日志。

    改进了异常处理：
    - 区分临时失败（可重试）和永久失败（需告警）
    - 记录完整异常栈
    - 返回结构化结果便于监控
    """
    import traceback
    try:
        result = fn()
        return {"name": name, "ok": True, "result": result}
    except Exception as exc:
        # 记录完整异常栈
        error_trace = traceback.format_exc()
        error_msg = str(exc)[:500]
        # 判断异常类型，决定日志级别
        if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
            # 临时性故障，记录 WARNING
            logger.warning(
                "Scheduler tick transient failure: name=%s error=%s\n%s",
                name,
                error_msg,
                error_trace,
            )
        else:
            # 永久性故障，记录 ERROR
            logger.error(
                "Scheduler tick permanent failure: name=%s error=%s\n%s",
                name,
                error_msg,
                error_trace,
            )

        return {
            "name": name,
            "ok": False,
            "error": error_msg,
            "error_type": type(exc).__name__,
        }


@shared_task(
    bind=True,
    name="app.tasks.ops_scheduler_tasks.paperclip_heartbeat_tick",
    max_retries=0,
)
def paperclip_heartbeat_tick(self):
    """D1: Paperclip agent heartbeat under Beat (no API daemon thread)."""
    from app.core.config import settings
    if not bool(getattr(settings, "SCHEDULER_BEAT_OWNS_ALL", True)):
        return

    from app.services.paperclip.agent import PaperclipAgent
    agent = PaperclipAgent()
    _safe_run("paperclip_heartbeat", agent.heartbeat)
