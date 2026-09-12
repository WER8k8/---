"""运维定时任务入口（需超管）— 供 cron / 手动触发。"""

import re
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.data_export_guard import assert_export_allowed
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.finance_service import FinanceService
from app.services.ops_backup_service import backup_status, run_manual_backup
from app.services.ops_readiness_alert_service import notify_readiness_if_unready
from app.services.production_readiness_service import (
    check_mounted_routes,
    run_readiness_checks,
)
from app.services.seven_step_framework_service import run_seven_step_audit
from app.services.super_admin_path_audit import run_super_admin_path_audit
from app.services.tenant_lifecycle_service import TenantLifecycleService
from app.services.publish_queue_service import (
    queue_stats,
    requeue_retryable_failed,
)
from app.workers.publish_worker import run_process_pending_tasks


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/ops", tags=["运维任务"])


def _admin_only(user: User):
    """执行 admin_only 相关逻辑处理。
    
    :param user: 用户对象
    :return: 返回处理结果。
    """
    if user.role not in ("admin", "super_admin"):
        return error_response(403, "仅超管可执行运维任务")
    return None


@router.get("/readiness")
def ops_readiness(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生产就绪检查（超管）。"""
    if err := _admin_only(current_user):
        return err
    report = run_readiness_checks(db)
    route_check = check_mounted_routes()
    report.add(route_check)
    return success_response(data=report.to_dict())


@router.get("/readiness/public")
def ops_readiness_public(db: Session = Depends(get_db)):
    """轻量就绪探针（无认证，供监控拉取）。"""
    report = run_readiness_checks(db)
    return success_response(
        data={
            "ready": report.ready,
            "environment": report.to_dict()["environment"],
            "score": report.score,
        }
    )


@router.post("/backup/run")
def ops_backup_run(current_user: User = Depends(get_current_user)):
    """处理 POST /backup/run 请求，ops相关资源。
    
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    try:
        result = run_manual_backup()
        return success_response(data=result, message="备份已完成")
    except Exception as exc:
        return error_response(500, str(exc))


@router.get("/backup/status")
def ops_backup_status(current_user: User = Depends(get_current_user)):
    """处理 GET /backup/status 请求，ops相关资源。
    
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    return success_response(data=backup_status())


@router.post("/ai-scenario-health/run")
def ops_ai_scenario_health_run(current_user: User = Depends(get_current_user)):
    """立即执行 AI 场景健康巡检并写入快照（供 cron / 手动）。"""
    if err := _admin_only(current_user):
        return err
    from app.services.scenario_health_scheduler import run_scenario_health_check
    report = run_scenario_health_check()
    return success_response(
        data={
            "healthy_count": report.get("healthy_count"),
            "unhealthy_count": report.get("unhealthy_count"),
            "saved_at": report.get("saved_at"),
        },
        message="场景健康巡检已完成",
    )


@router.get("/ai-scenario-health/status")
def ops_ai_scenario_health_status(current_user: User = Depends(get_current_user)):
    """处理 GET /ai-scenario-health/status 请求，ops相关资源。
    
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    from app.services.scenario_health_scheduler import scenario_health_scheduler
    return success_response(data=scenario_health_scheduler.status())


@router.post("/nvidia-customer-probe/run")
def ops_nvidia_customer_probe_run(current_user: User = Depends(get_current_user)):
    """立即探测英伟达客户可用模型（供 cron / 手动）。"""
    if err := _admin_only(current_user):
        return err
    from app.services.nvidia_customer_probe_scheduler import run_nvidia_customer_probe_manual
    report = run_nvidia_customer_probe_manual()
    return success_response(
        data={
            "healthy_count": report.get("healthy_count"),
            "unhealthy_count": report.get("unhealthy_count"),
            "saved_at": report.get("saved_at"),
            "available_scenarios": report.get("available_scenarios"),
        },
        message="英伟达客户可用模型探测已完成",
    )


@router.get("/nvidia-customer-probe/status")
def ops_nvidia_customer_probe_status(current_user: User = Depends(get_current_user)):
    """处理 GET /nvidia-customer-probe/status 请求，ops相关资源。
    
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    from app.services.nvidia_customer_probe_scheduler import nvidia_customer_probe_scheduler
    return success_response(data=nvidia_customer_probe_scheduler.status())


@router.get("/hermes-patrol/constitution")
def ops_hermes_patrol_constitution(current_user: User = Depends(get_current_user)):
    """Hermes 巡站维护宪法（只维护、不破坏）。"""
    if err := _admin_only(current_user):
        return err
    from app.services.hermes.maintenance_constitution import constitution_payload
    return success_response(data=constitution_payload())


@router.get("/hermes-patrol/status")
def ops_hermes_patrol_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /hermes-patrol/status 请求，ops相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    from app.services.hermes.site_patrol_service import patrol_status
    return success_response(data=patrol_status(db))


@router.post("/hermes-patrol/run")
def ops_hermes_patrol_run(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """立即执行一轮 Hermes 巡站（只读探测 + 快照，不修改业务数据）。"""
    if err := _admin_only(current_user):
        return err
    from app.services.hermes.site_patrol_service import run_site_patrol
    report = run_site_patrol(db, trigger="ops_manual")
    return success_response(
        data={
            "overall_status": report.get("overall_status"),
            "pass_count": report.get("pass_count"),
            "fail_count": report.get("fail_count"),
            "saved_at": report.get("saved_at"),
            "suggestions": report.get("suggestions"),
        },
        message="Hermes 巡站已完成（仅维护探测，未执行任何破坏性操作）",
    )


class OpsHermesInstructBody(BaseModel):
    command: str = Field(..., min_length=1, max_length=64)


@router.get("/hermes-ops/latest")
def ops_hermes_ops_latest(current_user: User = Depends(get_current_user)):
    """处理 GET /hermes-ops/latest 请求，ops相关资源。
    
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    from app.services.hermes.ops_autopilot import load_ops_snapshot
    return success_response(data=load_ops_snapshot() or {})


@router.post("/hermes-ops/run")
def ops_hermes_ops_run(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """完整 Hermes 运维循环（技术雷达 + 巡站 + 安全自愈 + 通知）。"""
    if err := _admin_only(current_user):
        return err
    from app.services.hermes.ops_autopilot import run_full_ops_cycle
    report = run_full_ops_cycle(db, trigger="ops_manual")
    patrol = report.get("patrol") or {}
    return success_response(
        data={
            "saved_at": report.get("saved_at"),
            "overall_status": patrol.get("overall_status"),
            "pass_count": patrol.get("pass_count"),
            "fail_count": patrol.get("fail_count"),
            "tech_high_impact": (report.get("tech_radar") or {}).get("high_impact_count"),
            "remediation": report.get("remediation"),
            "alert": report.get("alert"),
        },
        message="Hermes 运维循环已完成",
    )


@router.post("/hermes-ops/instruct")
def ops_hermes_ops_instruct(
    body: OpsHermesInstructBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /hermes-ops/instruct 请求，ops相关资源。
    
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    from app.services.hermes.safe_remediation import execute_human_instruction
    outcome = execute_human_instruction(db, body.command.strip())
    if outcome.get("error"):
        return error_response(400, outcome["error"], data=outcome)
    return success_response(data=outcome, message=f"已执行: {body.command.strip()}")


@router.get("/deerflow-schedule/status")
def ops_deerflow_schedule_status(current_user: User = Depends(get_current_user)):
    """处理 GET /deerflow-schedule/status 请求，ops相关资源。
    
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    from app.services.ubrain.deerflow_scheduled_service import load_deerflow_schedule_snapshot
    from app.services.ubrain.deerflow_scheduler import deerflow_scheduler
    return success_response(
        data={
            "scheduler": deerflow_scheduler.status(),
            "latest": load_deerflow_schedule_snapshot() or {},
        }
    )


@router.post("/deerflow-schedule/run")
def ops_deerflow_schedule_run(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /deerflow-schedule/run 请求，ops相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    from app.services.ubrain.deerflow_scheduled_service import run_scheduled_deerflow_update
    report = run_scheduled_deerflow_update(db, trigger="ops_manual", force=True)
    return success_response(data=report, message="DeerFlow 定时市场研究已执行")


@router.get("/trade-intel/status")
def ops_trade_intel_status(current_user: User = Depends(get_current_user)):
    """处理 GET /trade-intel/status 请求，ops相关资源。
    
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    from app.services.trade_intel_refresh_service import load_refresh_snapshot
    from app.services.trade_intel_scheduler import trade_intel_scheduler
    return success_response(
        data={
            "scheduler": trade_intel_scheduler.status(),
            "latest": load_refresh_snapshot() or {},
        }
    )


@router.post("/trade-intel/refresh")
def ops_trade_intel_refresh(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """立即从 UN Comtrade 刷新海关公开统计（供 cron / 手动）。"""
    if err := _admin_only(current_user):
        return err
    from app.services.trade_intel_scheduler import trade_intel_scheduler
    report = trade_intel_scheduler.run_once(trigger="ops_manual")
    return success_response(
        data=report,
        message="海关公开统计已刷新",
    )


@router.post("/media-cleanup/run")
def ops_media_cleanup_run(current_user: User = Depends(get_current_user)):
    """立即清理已过期的视频成品文件。"""
    if err := _admin_only(current_user):
        return err
    from app.core.database import SessionLocal
    from app.services.media_retention_service import run_media_cleanup
    db = SessionLocal()
    try:
        report = run_media_cleanup(db)
    finally:
        db.close()
    return success_response(data=report, message="视频成品清理已完成")


@router.get("/media-cleanup/status")
def ops_media_cleanup_status(current_user: User = Depends(get_current_user)):
    """处理 GET /media-cleanup/status 请求，ops相关资源。
    
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    from app.services.media_cleanup_scheduler import media_cleanup_scheduler
    return success_response(data=media_cleanup_scheduler.status())


@router.post("/alerts/readiness-notify")
def ops_readiness_notify(
    force: bool = Query(False, description="就绪时也发送摘要（测试用）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """未就绪时向飞书 Webhook 推送告警（OPS_READINESS_WEBHOOK_URL 或 FEISHU_WEBHOOK_URL）。"""
    if err := _admin_only(current_user):
        return err
    result = notify_readiness_if_unready(db, force=force)
    return success_response(data=result, message="告警处理完成")


@router.post("/tenants/enforce-expiry")
def enforce_tenant_expiry(
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /tenants/enforce-expiry 请求，enforce相关资源。
    
    :param dry_run: 是否试运行
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    result = TenantLifecycleService(db).run_all(dry_run=dry_run)
    return success_response(data=result, message="租户到期检查完成")


@router.get("/fcm/status")
def ops_fcm_status(current_user: User = Depends(get_current_user)):
    """APP-1b：FCM Push 配置状态。"""
    from app.services.push_notification_service import fcm_enabled
    if err := _admin_only(current_user):
        return err
    return success_response(
        data={
            "fcm_configured": fcm_enabled(),
            "env_key": "FCM_SERVER_KEY",
            "legacy_endpoint": "https://fcm.googleapis.com/fcm/send",
        }
    )


@router.get("/smtp/status")
def ops_smtp_status(current_user: User = Depends(get_current_user)):
    """P1-07：SMTP 发信配置探针。"""
    from app.services.email_service import email_service
    if err := _admin_only(current_user):
        return err
    return success_response(data=email_service.smtp_status())


@router.post("/platforms/seed-full")
def ops_seed_platforms_full(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """P1-10：将 40 平台 catalog 写入 DB。"""
    from app.services.platform_alignment_service import seed_full_platforms
    if err := _admin_only(current_user):
        return err
    result = seed_full_platforms(db)
    return success_response(
        data=result,
        message="平台 seed 完成" if result.get("alignment", {}).get("aligned") else "seed 完成，仍有未对齐项",
    )


@router.get("/super-admin/path-audit")
def ops_super_admin_path_audit(
    current_user: User = Depends(get_current_user),
):
    """P0-08：对比前端 super-admin 引用与后端挂载（0 missing = 通过）。"""
    if err := _admin_only(current_user):
        return err
    data = run_super_admin_path_audit()
    return success_response(
        data=data,
        message="路径对齐" if data.get("ok") else f"缺失 {data.get('missing_count')} 条",
    )


@router.get("/publish-worker/status")
def ops_publish_worker_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布队列深度（P0-03）。"""
    if err := _admin_only(current_user):
        return err
    return success_response(data=queue_stats(db))


@router.post("/publish-worker/retry-failed")
def ops_publish_worker_retry_failed(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """将可重试的失败任务重新入队。"""
    if err := _admin_only(current_user):
        return err
    n = requeue_retryable_failed(db, limit=limit)
    return success_response(data={"requeued": n}, message=f"已重新入队 {n} 条")


@router.post("/publish-worker/run")
def ops_publish_worker_run(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """消费 pending 发布任务（供 cron / 手动触发）。"""
    if err := _admin_only(current_user):
        return err
    stats = run_process_pending_tasks(db, limit=limit)
    stats["queue"] = queue_stats(db)
    return success_response(data=stats, message="发布队列已处理")


@router.get("/tenants/expiry-preview")
def ops_tenant_expiry_preview(
    within_days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """即将到期租户列表（P0-06，不执行冻结）。"""
    if err := _admin_only(current_user):
        return err
    data = TenantLifecycleService(db).preview_expiring(within_days=within_days)
    return success_response(data=data)


@router.post("/jobs/run-all")
def ops_run_all_jobs(
    dry_run: bool = Query(False),
    publish_limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """一键运维批处理：到期冻结 + AI 成本归集 + 发布队列。"""
    if err := _admin_only(current_user):
        return err
    expiry = TenantLifecycleService(db).run_all(dry_run=dry_run)
    costs = FinanceService(db).sync_ai_model_costs(dry_run=dry_run)
    publish = (
        {"processed": 0, "success": 0, "failed": 0, "skipped": dry_run}
        if dry_run
        else run_process_pending_tasks(db, limit=publish_limit)
    )
    return success_response(
        data={
            "tenant_expiry": expiry,
            "ai_costs": costs,
            "publish_worker": publish,
            "dry_run": dry_run,
        },
        message="运维批处理完成",
    )


@router.post("/finance/sync-ai-costs")
def sync_ai_costs(
    day: Optional[str] = Query(None, description="YYYY-MM-DD，默认今天"),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /finance/sync-ai-costs 请求，同步相关资源。
    
    :param day: 参数 day
    :param dry_run: 是否试运行
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    target = date.fromisoformat(day) if day else None
    result = FinanceService(db).sync_ai_model_costs(day=target, dry_run=dry_run)
    return success_response(data=result, message="AI 成本归集完成")


@router.get("/finance/export-ledger.csv")
def export_ledger_csv(
    request: Request,
    entry_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /finance/export-ledger.csv 请求，导出相关资源。
    
    :param request: HTTP 请求对象
    :param entry_type: 参数 entry_type
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    assert_export_allowed(
        db,
        current_user,
        request,
        export_kind="finance_ledger_csv",
        scope="platform",
    )
    csv_text = FinanceService(db).export_ledger_csv(entry_type=entry_type)
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="finance_ledger.csv"'},
    )


_FRONTEND_ROOT = Path(__file__).resolve().parents[5] / "frontend"
_SA_PATH_RE = re.compile(
    r"""['"](/api/v1/super-admin[^'"]+)['"]|"""
    r"""['"`](/super-admin[^'"]+)['"`]"""
)


def _collect_super_admin_frontend_paths() -> set[str]:
    """执行 collect_super_admin_frontend_paths 相关逻辑处理。
    :return: 返回处理结果。
    """
    found: set[str] = set()
    for base in (_FRONTEND_ROOT / "admin", _FRONTEND_ROOT / "pages"):
        if not base.is_dir():
            continue
        for ext in ("*.vue", "*.ts", "*.js"):
            for path in base.rglob(ext):
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for m in _SA_PATH_RE.finditer(text):
                    p = m.group(1) or m.group(2)
                    if p.startswith("/api/v1"):
                        p = p[len("/api/v1") :]
                    if not p.startswith("/super-admin"):
                        continue
                    found.add(p.split("?")[0].rstrip("/") or p)
    return found


class DouyinCommentBatchBody(BaseModel):
    items: list[dict] = Field(..., min_length=0, max_length=500)


@router.post("/jobs/douyin-comment-pull")
async def ops_douyin_comment_pull(
    tenant_id: str,
    source: str = "auto",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管/cron：从 AiToEarn 或 Inbox 拉评并入库（ITER-03b）。"""
    if err := _admin_only(current_user):
        return err
    from app.services.douyin_comment_pull_service import pull_and_ingest_for_tenant
    if source not in ("auto", "aitoearn", "inbox"):
        return error_response(400, "source 须为 auto|aitoearn|inbox")
    result = await pull_and_ingest_for_tenant(db, tenant_id, source=source)
    return success_response(data=result, message="抖音评论拉取完成")


@router.post("/jobs/douyin-comment-sync")
def ops_douyin_comment_sync(
    body: DouyinCommentBatchBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管：批量同步抖音评论 → social_interactions（供 Worker/cron 调用）。"""
    if err := _admin_only(current_user):
        return err
    from app.services.douyin_comment_sync_service import ingest_batch_internal, normalize_batch_item
    normalized = []
    errors = []
    for i, raw in enumerate(body.items):
        try:
            normalized.append(normalize_batch_item(raw))
        except ValueError as exc:
            errors.append({"index": i, "error": str(exc)})
    if errors and not normalized:
        return error_response(400, f"批处理无效: {errors[:3]}")
    result = ingest_batch_internal(db, normalized)
    if errors:
        result["validation_errors"] = errors[:10]
    return success_response(data=result, message="抖音评论同步完成")


@router.get("/demo-checklist")
def ops_demo_checklist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """七步商用彩排清单（P0 彩排，超管可读）。"""
    if err := _admin_only(current_user):
        return err
    report = run_readiness_checks(db)
    audit = run_seven_step_audit(db)
    steps = [
        {"step": 1, "name": "开通 SaaS", "check": "租户注册 + 套餐", "path": "/tenants/register"},
        {"step": 2, "name": "独立域 HTTPS", "check": "SSL_PROVIDER / 演示域 DNS", "path": "/admin/platform-zones"},
        {"step": 3, "name": "统一母版发布", "check": "发布 Worker cron", "path": "/ops/publish-worker/run"},
        {"step": 4, "name": "40 平台", "check": "platforms seed", "path": "/api/v1/platforms/catalog"},
        {
            "step": 5,
            "name": "询盘 IM",
            "check": "5a 入站 webhook · 5b 租户企微推送 · 5c 抖音评论/自动谈单",
            "path": "/api/v1/inquiries/channels/wecom",
            "substeps": [
                {"id": "5a", "name": "客户能联系到你", "path": "/inquiries/im-routing", "api": "/api/v1/inquiries/channels/wecom"},
                {"id": "5b", "name": "销售收得到通知", "path": "/inquiries/im-routing#wecom-push", "api": "/api/v1/client/wecom-push-config"},
                {"id": "5c", "name": "抖音评论自动抓", "path": "/sales/auto-negotiator", "api": "/api/v1/social-interactions/worker/config"},
            ],
            "qa_doc": "docs/qa-step5-inquiry-im-acceptance.md",
            "screenshot_dir": "docs/mod-04-rehearsal/step5/",
        },
        {"step": 6, "name": "订单报价", "check": "PATCH payment-status + 支付回调联动", "path": "/api/v1/orders/"},
        {"step": 7, "name": "物流与助手", "check": "UBrain + 出海参谋 + 物流看板", "path": "/client/assistant"},
    ]
    return success_response(
        data={
            "steps": steps,
            "automated_audit": audit,
            "readiness": report.to_dict(),
            "recording_hint": "按 steps 1→7 录屏；可先 GET /ops/seven-steps/audit 查看自动探针",
        }
    )


@router.get("/seven-steps/audit")
def ops_seven_steps_audit(
    demo_domain: Optional[str] = Query(None, description="临时演示域，用于 HTTPS 探针（不写入环境变量）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """商用七步主链自动验收（框架 P0 优先）。"""
    if err := _admin_only(current_user):
        return err
    return success_response(data=run_seven_step_audit(db, demo_domain=demo_domain))


@router.get("/super-admin-route-audit")
def super_admin_route_audit(
    current_user: User = Depends(get_current_user),
):
    """对照管理端 fetch 路径与已挂载超管 API（P0-08）。"""
    if err := _admin_only(current_user):
        return err
    from app.main import app
    mounted = {
        (getattr(r, "path", "") or "").rstrip("/")
        for r in app.routes
        if (getattr(r, "path", "") or "").startswith("/api/v1/super-admin")
    }
    frontend_calls = _collect_super_admin_frontend_paths()
    missing = sorted(
        p
        for p in frontend_calls
        if not any(m == p or m.startswith(p + "/") for m in mounted)
    )
    return success_response(
        data={
            "frontend_call_count": len(frontend_calls),
            "mounted_super_admin_count": len(mounted),
            "possibly_missing": missing[:80],
            "missing_count": len(missing),
        }
    )
