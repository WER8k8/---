# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 内部插件平台 API — 运维/编排；租户侧请用旺财插件市场。"""

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any

from app.core.config import settings
from app.core.response import error_json_response, error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.hermes.brand_guard import sanitize_public_data
from app.services.hermes.flywheel_workflow import public_flywheel_status
from app.services.hermes.install_service import list_tenant_installs
from app.services.hermes.registry import (
    catalog_meta,
    internal_plugin_item,
    list_plugins,
)
from app.services.hermes.runtime import HermesPluginError, execute_plugin
from app.services.ubrain.action_audit_service import log_action
from app.services.hermes.ops_access import is_ops_admin, ops_admin_forbidden_message
from app.api.v1.routes.ubrain import _resolve_tenant_id


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/hermes", tags=["Hermes插件平台"])


def _ops_gate(user: User):
    """
    处理 _ops_gate 相关业务逻辑。

    :param user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if not is_ops_admin(user):
        return error_response(403, ops_admin_forbidden_message())
    return None


def _greedy_gate():
    """
    处理 _greedy_gate 相关业务逻辑。

    :return: 返回处理结果（或 None）。
    """
    from app.core.config import settings as cfg
    if not cfg.HERMES_GREEDY_AVATAR_ENABLED:
        return error_response(503, "财迷疯分身未启用（HERMES_GREEDY_AVATAR_ENABLED=false）")
    return None


def _require_cron(request: Request):
    """校验 OPS_CRON_TOKEN（未配置则不校验）。"""
    from app.core.config import settings as cfg
    token = (cfg.OPS_CRON_TOKEN or "").strip()
    if not token:
        return None
    auth = request.headers.get("authorization", "")
    if auth == f"Bearer {token}" or auth == token:
        return None
    return error_response(403, "无效的 cron token")


def _run_ops_cycle_background(trigger: str) -> None:
    """
    处理 _run_ops_cycle_background 相关业务逻辑。

    :param trigger: 入参 (str)。

    :return: 返回 None 类型的结果。
    """
    from app.core.database import SessionLocal
    from app.services.hermes.command_center_cache import warm_command_center_snapshot
    from app.services.hermes.ops_autopilot import run_full_ops_cycle
    db = SessionLocal()
    try:
        run_full_ops_cycle(db, trigger=trigger)
        warm_command_center_snapshot(reason=f"post_ops:{trigger}")
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Hermes ops background run failed: %s", exc)
    finally:
        db.close()


def _run_deerflow_background(trigger: str) -> None:
    """
    处理 _run_deerflow_background 相关业务逻辑。

    :param trigger: 入参 (str)。

    :return: 返回 None 类型的结果。
    """
    from app.core.database import SessionLocal
    from app.services.ubrain.deerflow_scheduled_service import run_scheduled_deerflow_update
    db = SessionLocal()
    try:
        run_scheduled_deerflow_update(db, trigger=trigger, force=True)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("DeerFlow background run failed: %s", exc)
    finally:
        db.close()


def _run_continuous_iteration_background(trigger: str, *, force: bool = False) -> None:
    """
    处理 _run_continuous_iteration_background 相关业务逻辑。

    :param trigger: 入参 (str)。
    :param force: 入参 (bool)。

    :return: 返回 None 类型的结果。
    """
    from app.core.database import SessionLocal
    from app.services.hermes.hermes_continuous_iteration_service import run_continuous_iteration_cycle
    db = SessionLocal()
    try:
        run_continuous_iteration_cycle(db, trigger=trigger, force=force)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Hermes continuous iteration background run failed: %s", exc)
    finally:
        db.close()


class FlywheelRunRequest(BaseModel):
    message: str = Field(
        default="跑一轮市场研究并自动找客",
        min_length=1,
        max_length=2000,
    )


@router.get("/plugins/catalog")
def hermes_plugin_catalog(
    visibility: str | None = Query(None, description="public | internal | 空=全部"),
    current_user: User = Depends(get_current_user),
):
    """对内完整插件目录（含 handler / lane）。"""
    if visibility == "public":
        items = [internal_plugin_item(p) for p in list_plugins(visibility="public")]
    elif visibility == "internal":
        items = [internal_plugin_item(p) for p in list_plugins(visibility="internal")]
    else:
        items = [internal_plugin_item(p) for p in list_plugins()]
    return success_response(data={"meta": catalog_meta(), "items": items})


class PluginRunBody(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    context: dict | None = None


@router.post("/plugins/{plugin_id}/run")
def hermes_plugin_run(
    plugin_id: str,
    body: PluginRunBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 hermes_plugin_run 相关业务逻辑。

    :param plugin_id: 入参 (str)。
    :param body: 入参 (PluginRunBody)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    try:
        data = execute_plugin(
            db,
            tenant_id=str(tenant_id),
            plugin_id=plugin_id,
            message=body.message,
            context=body.context,
            user_id=str(current_user.id) if current_user else None,
        )
    except HermesPluginError as exc:
        return error_response(400, str(exc))
    return success_response(data=sanitize_public_data(data))


class AgencyWorkflowRunBody(BaseModel):
    message: str = Field(default="", max_length=4000)
    context: dict | None = None
    inputs: dict | None = None


@router.get("/agency/providers/setup-plan")
def hermes_agency_setup_plan(
    target: str = Query("server", description="server | dev"),
    current_user: User = Depends(get_current_user),
):
    """agency LLM 安装计划：可脚本化步骤 + 需人工 OAuth/API Key 步骤。"""
    from app.services.hermes.agency.provider_setup import build_setup_plan
    if target not in ("server", "dev"):
        target = "server"
    return success_response(data=build_setup_plan(target=target))


@router.post("/agency/providers/bootstrap")
def hermes_agency_bootstrap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管：执行无 OAuth 的 bootstrap（ollama pull 等）。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.agency.provider_setup import run_automated_bootstrap
    return success_response(data=run_automated_bootstrap())


@router.get("/agency/providers")
def hermes_agency_providers(
    probe: bool = Query(True, description="是否探测 CLI/Key/Ollama 可用性"),
    current_user: User = Depends(get_current_user),
):
    """ao 10 种 LLM provider + 7 种免 Key 通道状态。"""
    from app.services.hermes.agency.llm_router import list_providers, provider_catalog_meta
    return success_response(
        data={
            "meta": provider_catalog_meta(),
            "providers": list_providers(probe=probe),
        }
    )


@router.get("/agency/catalog")
def hermes_agency_catalog(
    include_roles: bool = Query(True, description="false 时仅返回 meta + workflows，减轻响应体"),
    current_user: User = Depends(get_current_user),
):
    """Hermes 内嵌专家角色库与工作流目录（agency-orchestrator 全量资产）。"""
    from app.services.hermes.agency.orchestrator_bridge import agency_catalog
    return success_response(data=agency_catalog(include_roles=include_roles))


@router.post("/agency/workflows/{workflow_id}/run")
async def hermes_agency_workflow_run(
    workflow_id: str,
    body: AgencyWorkflowRunBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行指定 YAML 工作流（Hermes 驱动，多专家 DAG）。"""
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")

    from app.services.hermes.agency.orchestrator_bridge import (
        run_geo_matrix_via_agency,
        run_hermes_agency_workflow,
    )
    ctx = dict(body.context or {})
    if body.inputs:
        ctx.update(body.inputs)
    try:
        if workflow_id in ("geo-content-matrix-b2b", "geo_content_matrix_b2b"):
            data = await run_geo_matrix_via_agency(
                db,
                message=body.message or "GEO 内容矩阵",
                tenant_id=str(tenant_id),
                context=ctx,
                created_by=str(current_user.id) if current_user else None,
            )
        else:
            data = await run_hermes_agency_workflow(
                db,
                workflow_id=workflow_id,
                message=body.message or "",
                tenant_id=str(tenant_id),
                context=ctx,
            )
    except FileNotFoundError:
        return error_response(404, f"工作流不存在: {workflow_id}")
    except Exception as exc:
        return error_response(400, str(exc)[:200])
    return success_response(data=sanitize_public_data(data))


@router.get("/tenants/{tenant_id}/installs")
def hermes_tenant_installs(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 hermes_tenant_installs 相关业务逻辑。

    :param tenant_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if (current_user.role or "") not in ("admin", "super_admin"):
        resolved = _resolve_tenant_id(current_user, db)
        if str(resolved) != str(tenant_id):
            return error_response(403, "无权查看")
    rows = list_tenant_installs(db, tenant_id)
    return success_response(
        data={
            "items": [
                {
                    "plugin_id": r.plugin_id,
                    "version": r.plugin_version,
                    "enabled": r.enabled,
                    "installed_at": r.installed_at.isoformat() if r.installed_at else None,
                }
                for r in rows
            ]
        }
    )


@router.post("/flywheel/run")
def hermes_flywheel_run(
    body: FlywheelRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管内部同步飞轮；租户请走 POST /ubrain/chat（异步）。"""
    if err := _ops_gate(current_user):
        return err
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    user_id = str(current_user.id) if current_user else None
    try:
        data = execute_plugin(
            db,
            tenant_id=str(tenant_id),
            plugin_id="sales_flywheel_loop",
            message=body.message.strip(),
            user_id=user_id,
        )
    except HermesPluginError as exc:
        return error_response(400, str(exc))
    try:
        log_action(
            db,
            tenant_id=str(tenant_id),
            user_id=user_id,
            action_type="hermes_flywheel",
            intent="flywheel_loop",
            tool="hermes",
            message=body.message[:400],
            needs_confirmation=bool(data.get("needs_confirmation")),
            outcome="ok"
            if not (data.get("tool_result") or {}).get("errors")
            else "partial",
            meta={
                "plugin_id": "sales_flywheel_loop",
                "ticket_id": (data.get("tool_result") or {}).get("ticket_id"),
                "steps": len((data.get("tool_result") or {}).get("steps") or []),
            },
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Flywheel 结果保存失败: %s", exc)


@router.get("/flywheel/status")
def hermes_flywheel_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 hermes_flywheel_status 相关业务逻辑。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    return success_response(data=public_flywheel_status(db, str(tenant_id)))


@router.get("/patrol/constitution")
def hermes_patrol_constitution(current_user: User = Depends(get_current_user)):
    """维护宪法：只读探测边界（超管）。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.maintenance_constitution import constitution_payload
    return success_response(data=constitution_payload())


@router.get("/patrol/status")
def hermes_patrol_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 hermes_patrol_status 相关业务逻辑。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.site_patrol_service import patrol_status
    return success_response(data=patrol_status(db))


@router.post("/patrol/run")
def hermes_patrol_run(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 hermes_patrol_run 相关业务逻辑。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.site_patrol_service import run_site_patrol
    report = run_site_patrol(db, trigger="hermes_api")
    return success_response(
        data=report,
        message="巡站完成；未执行删改/发布/扣费等操作",
    )


class OpsInstructBody(BaseModel):
    command: str = Field(..., min_length=1, max_length=64, description="rerun_patrol | rerun_tech_radar | rerun_deerflow | deerflow_pending | full_cycle | ack")


@router.get("/ops/deerflow/status")
def hermes_ops_deerflow_status(current_user: User = Depends(get_current_user)):
    """
    处理 hermes_ops_deerflow_status 相关业务逻辑。

    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _ops_gate(current_user):
        return err
    from app.services.ubrain.deerflow_scheduled_service import load_deerflow_schedule_snapshot
    from app.services.ubrain.deerflow_scheduler import deerflow_scheduler
    return success_response(
        data={
            "scheduler": deerflow_scheduler.status(),
            "latest": load_deerflow_schedule_snapshot() or {},
        }
    )


@router.post("/ops/deerflow/run")
def hermes_ops_deerflow_run(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background: bool = Query(True, description="后台执行，避免 HTTP 超时"),
):
    """立即跑一轮 DeerFlow 定时市场研究（全活跃租户）。"""
    if err := _ops_gate(current_user):
        return err
    if background:
        background_tasks.add_task(_run_deerflow_background, "hermes_api")
        return success_response(
            data={"status": "started", "mode": "background"},
            message="DeerFlow 已在后台启动（约 1–3 分钟），请稍后点刷新查看队列",
        )
    from app.services.ubrain.deerflow_scheduled_service import run_scheduled_deerflow_update
    report = run_scheduled_deerflow_update(db, trigger="hermes_api", force=True)
    return success_response(
        data=report,
        message="市场研究定时任务已执行（洞察沉淀 + 队列消费）",
    )


@router.get("/ops/experts")
def hermes_ops_experts(current_user: User = Depends(get_current_user)):
    """ECC 专家人格 roster（Hermes 技术雷达只读评审）。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.ecc_expert_panel import panel_meta
    return success_response(data=panel_meta())


@router.get("/ops/latest")
def hermes_ops_latest(current_user: User = Depends(get_current_user)):
    """最近一次 Hermes 运维自动驾驶快照（技术雷达 + 巡站 + 自愈）。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.ops_autopilot import load_ops_snapshot
    return success_response(data=load_ops_snapshot() or {})


@router.get("/ops/command-center")
def hermes_ops_command_center(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    refresh: bool = Query(False, description="为 true 时跳过 30s 内存缓存"),
):
    """L0 超管司令部一页总览：Hermes + DeerFlow + SEO + 视频 Worker。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.command_center_cache import build_command_center_snapshot
    try:
        return success_response(data=build_command_center_snapshot(db, force_refresh=refresh))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("command_center aggregate failed")
        return error_json_response(
            503,
            f"司令部聚合暂时不可用：{str(exc)[:120]}",
        )


@router.post("/ops/rank-guard/check")
def hermes_ops_rank_guard_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SEO-06：立即运行 GEO Rank Guard 探针并刷新司令部快照。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.geo_rank_guard_probe import run_rank_guard_probe
    report = run_rank_guard_probe(db, trigger="hermes_api")
    return success_response(
        data=report,
        message="Rank Guard 检测完成" if report.get("passed") else "Rank Guard 未通过，已记录告警",
    )


@router.post("/ops/inclusion/recheck")
def hermes_ops_inclusion_recheck(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(30, ge=1, le=100),
):
    """SEO：超管触发收录复检（Baidu site: 探测）。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.seo.inclusion_check_service import recheck_inclusion_batch
    report = recheck_inclusion_batch(db, limit=limit)
    return success_response(
        data=report,
        message=f"收录复检完成：已收录 {report.get('included_count', 0)} / {report.get('updated_count', 0)}",
    )


@router.get("/ops/deerflow/jobs")
def hermes_ops_deerflow_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    status: str | None = Query(None),
    tenant_id: str | None = Query(None),
):
    """DF-10：超管 DeerFlow 队列分页 + 步骤卡。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.deerflow_ops_service import deerflow_slo_snapshot, list_ops_jobs
    data = list_ops_jobs(db, page=page, page_size=page_size, status=status, tenant_id=tenant_id)
    data["slo"] = deerflow_slo_snapshot(db)
    return success_response(data=data)


@router.get("/ops/publish-history")
def hermes_ops_publish_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(30, ge=1, le=100),
):
    """VID-09：SEO + 视频统一发布历史。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.publish_history_aggregate import list_unified_publish_history
    return success_response(data=list_unified_publish_history(db, limit=limit))


@router.get("/ops/rank-scheduler")
def hermes_ops_rank_scheduler(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SEO-04：Rank Scheduler 状态 + 最近排名 + DB 关键词数。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.seo.rank_scheduler_ops import build_rank_scheduler_ops_snapshot
    return success_response(data=build_rank_scheduler_ops_snapshot(db))


@router.post("/ops/rank-scheduler/sync")
def hermes_ops_rank_scheduler_sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从 keywords 表同步追踪词到内存 Rank Scheduler。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.seo.rank_scheduler_ops import sync_keywords_from_db
    report = sync_keywords_from_db(db)
    return success_response(
        data=report,
        message=f"已同步 {report.get('synced_items', 0)} 个关键词",
    )


@router.post("/ops/rank-scheduler/run")
def hermes_ops_rank_scheduler_run(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """立即执行一轮排名检查（未同步则先 sync）。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.seo.rank_scheduler_ops import run_rank_check_now
    report = run_rank_check_now(db)
    return success_response(
        data=report,
        message=f"排名检查完成：{report.get('checked', 0)} 个关键词",
    )


@router.get("/ops/brand-audit")
def hermes_ops_brand_audit(current_user: User = Depends(get_current_user)):
    """COMP-02：租户可见文案品牌禁词抽检。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.brand_audit_service import audit_brand_leaks
    report = audit_brand_leaks()
    return success_response(
        data=report,
        message="品牌抽检通过" if report.get("ok") else f"发现 {report.get('violations_count', 0)} 处疑似泄露",
    )


@router.get("/ops/seo-matrix-db/health")
def hermes_ops_seo_matrix_db_health(current_user: User = Depends(get_current_user)):
    """SEO-09：独立 SEO 矩阵库连通性。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.seo.seo_matrix_db_health import seo_matrix_db_health
    report = seo_matrix_db_health()
    return success_response(data=report)


@router.get("/ops/tech-radar/reports")
def hermes_ops_tech_radar_reports(
    current_user: User = Depends(get_current_user),
    limit: int = Query(14, ge=1, le=60),
):
    """RADAR-06：最近技术雷达 Markdown 日报索引。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.geo.tech_radar_reports_service import list_tech_radar_reports
    return success_response(data=list_tech_radar_reports(limit=limit))


@router.get("/ops/write-boundary-audit")
def hermes_ops_write_boundary_audit(current_user: User = Depends(get_current_user)):
    """ARCH-03：Hermes 写库边界静态审计。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.write_boundary_audit_service import audit_write_boundaries
    report = audit_write_boundaries()
    return success_response(
        data=report,
        message="写库边界通过" if report.get("ok") else f"发现 {report.get('violations_count', 0)} 项",
    )


@router.post("/ops/integrations/mem0/sync")
def hermes_ops_mem0_sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(25, ge=1, le=100),
):
    """INT-03：批量双写最近洞察至 Mem0（未配置则 no-op）。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.ubrain.mem0_batch_sync_service import sync_recent_insights_to_mem0
    report = sync_recent_insights_to_mem0(db, limit=limit)
    return success_response(
        data=report,
        message=f"Mem0 同步：{report.get('synced', 0)}/{report.get('total', 0)}",
    )


@router.post("/ops/run")
def hermes_ops_run(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background: bool = Query(True, description="后台执行，避免 HTTP 超时"),
):
    """立即跑完整运维循环：技术雷达 → 巡站 → 安全自愈 → 飞书（异常时）。"""
    if err := _ops_gate(current_user):
        return err
    if background:
        from app.services.hermes.command_center_cache import invalidate_command_center_cache
        invalidate_command_center_cache()
        background_tasks.add_task(_run_ops_cycle_background, "hermes_api")
        return success_response(
            data={"status": "started", "mode": "background"},
            message="Hermes 运维循环已在后台启动（约 1–3 分钟），请稍后点刷新",
        )
    from app.services.hermes.ops_autopilot import run_full_ops_cycle
    report = run_full_ops_cycle(db, trigger="hermes_api")
    patrol = report.get("patrol") or {}
    return success_response(
        data={
            "saved_at": report.get("saved_at"),
            "patrol_status": patrol.get("overall_status"),
            "pass_count": patrol.get("pass_count"),
            "fail_count": patrol.get("fail_count"),
            "tech_high_impact": (report.get("tech_radar") or {}).get("high_impact_count"),
            "remediation": report.get("remediation"),
            "alert": report.get("alert"),
            "continuous_iteration": report.get("continuous_iteration"),
        },
        message="Hermes 运维循环已完成（仅白名单自愈，无删改/发版）",
    )


@router.get("/ops/continuous-iteration")
def hermes_continuous_iteration_status(
    current_user: User = Depends(get_current_user),
):
    """研究员×ECC×各部门迭代状态与 PM Inbox 预览。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.hermes_continuous_iteration_service import iteration_status
    return success_response(data=iteration_status(), message="持续迭代状态")


@router.get("/ops/marketing/monetize-workflow")
def hermes_marketing_monetize_workflow_status(
    current_user: User = Depends(get_current_user),
):
    """Hermes 营销 Lane：数字产品/智能体变现 AnySearch 工作流定义与最近快照。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.marketing_anysearch_workflow_service import workflow_status
    return success_response(data=workflow_status(), message="营销变现工作流状态")


@router.post("/ops/marketing/monetize-workflow/run")
def hermes_marketing_monetize_workflow_run(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background: bool = Query(True),
    max_rounds: int | None = Query(None, ge=1, le=8),
):
    """跑 monetize 计划：AnySearch 八轮 → 深度拆解 → ECC → 营销/PM 路由（只读，不自动发布）。"""
    if err := _ops_gate(current_user):
        return err

    def _bg(max_r: int | None) -> None:
        """
        处理 _bg 相关业务逻辑。

        :param max_r: 入参 (int | None)。

        :return: 返回 None 类型的结果。
        """
        from app.db.session import SessionLocal
        from app.services.hermes.marketing_anysearch_workflow_service import run_monetize_workflow
        sdb = SessionLocal()
        try:
            run_monetize_workflow(sdb, max_rounds=max_r, trigger="hermes_api")
        finally:
            sdb.close()

    if background:
        background_tasks.add_task(_bg, max_rounds)
        return success_response(
            data={"status": "started", "mode": "background", "max_rounds": max_rounds},
            message="营销 AnySearch 变现工作流已在后台启动（约 3–8 分钟）",
        )
    from app.services.hermes.marketing_anysearch_workflow_service import run_monetize_workflow
    report = run_monetize_workflow(db, max_rounds=max_rounds, trigger="hermes_api")
    return success_response(
        data={
            "rounds": len(report.get("rounds") or []),
            "workflow_blueprint": report.get("workflow_blueprint"),
            "executive_summary": report.get("executive_summary"),
        },
        message="营销变现工作流已完成",
    )


@router.post("/ops/continuous-iteration/run")
def hermes_continuous_iteration_run(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background: bool = Query(True),
    force: bool = Query(False, description="忽略小时去重"),
):
    """跑一轮：ResearchBrief → ECC → 部门路由 → Inbox（违宪动作不执行）。"""
    if err := _ops_gate(current_user):
        return err
    if background:
        background_tasks.add_task(_run_continuous_iteration_background, "hermes_api", force=force)
        return success_response(
            data={"status": "started", "mode": "background", "force": force},
            message="持续迭代已在后台启动",
        )
    from app.services.hermes.hermes_continuous_iteration_service import run_continuous_iteration_cycle
    report = run_continuous_iteration_cycle(db, trigger="hermes_api", force=force)
    return success_response(
        data={
            "skipped": report.get("skipped"),
            "brief_id": (report.get("brief") or {}).get("brief_id"),
            "ecc_verdict": (report.get("ecc") or {}).get("verdict"),
            "departments": [d.get("seat") for d in report.get("department_routing") or []],
            "a2a_skill": ((report.get("a2a") or {}).get("skill_listed") or {}).get("skill_id"),
            "revenue_progress_pct": (
                ((report.get("a2a") or {}).get("survival_pulse") or {}).get("progress_pct")
                or ((report.get("a2a") or {}).get("revenue_pulse_legacy_estimated") or {}).get("progress_pct")
            ),
        },
        message="持续迭代已完成" if not report.get("skipped") else f"已跳过：{report.get('reason')}",
    )


class A2ANegotiateBody(BaseModel):
    consumer_agent_id: str = Field(..., min_length=2, max_length=64)
    skill_id: str = Field(..., min_length=4, max_length=128)
    max_credits: int | None = Field(default=None, ge=1, le=500)


@router.get("/a2a/status")
def hermes_a2a_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """A2A 经济体状态 + 财迷疯收益脉搏。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.a2a_skill_marketplace_service import a2a_status
    return success_response(data=a2a_status(db))


@router.get("/a2a/agents")
def hermes_a2a_agents(current_user: User = Depends(get_current_user)):
    """
    处理 hermes_a2a_agents 相关业务逻辑。

    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.a2a_skill_marketplace_service import list_a2a_agents, load_a2a_registry
    reg = load_a2a_registry()
    return success_response(
        data={
            "agents": list_a2a_agents(),
            "daily_target_cny": reg.get("daily_target_cny"),
            "legal_only": reg.get("legal_only"),
        }
    )


@router.get("/a2a/skills")
def hermes_a2a_skills(
    current_user: User = Depends(get_current_user),
    limit: int = Query(30, ge=1, le=100),
    seat: str | None = Query(None),
):
    """
    处理 hermes_a2a_skills 相关业务逻辑。

    :param current_user: 入参 (User)。
    :param limit: 入参 (int)。
    :param seat: 入参 (str | None)。

    :return: 返回处理结果（或 None）。
    """
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.a2a_skill_marketplace_service import list_a2a_skills
    return success_response(data={"items": list_a2a_skills(limit=limit, seat=seat)})


@router.get("/a2a/tasks")
def hermes_a2a_tasks(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=50),
):
    """
    处理 hermes_a2a_tasks 相关业务逻辑。

    :param current_user: 入参 (User)。
    :param limit: 入参 (int)。

    :return: 返回处理结果（或 None）。
    """
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.a2a_skill_marketplace_service import list_open_tasks
    return success_response(data={"items": list_open_tasks(limit=limit)})


@router.get("/a2a/revenue-pulse")
def hermes_a2a_revenue_pulse(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 hermes_a2a_revenue_pulse 相关业务逻辑。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.a2a_skill_marketplace_service import revenue_pulse
    return success_response(data=revenue_pulse(db))


@router.post("/a2a/negotiate")
def hermes_a2a_negotiate(
    body: A2ANegotiateBody,
    current_user: User = Depends(get_current_user),
):
    """Agent 间议价 → 虚拟积分结算预览（不打真款）。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.a2a_skill_marketplace_service import negotiate_a2a_task
    return success_response(
        data=negotiate_a2a_task(
            consumer_agent_id=body.consumer_agent_id.strip(),
            skill_id=body.skill_id.strip(),
            max_credits=body.max_credits,
        ),
        message="A2A 议价结果为历史虚拟积分预览；生存 KPI 以 /ops/survival 真钱台账为准",
    )


class SurvivalRecordBody(BaseModel):
    amount_minor: int = Field(..., ge=1, description="最小货币单位，如 CNY 分")
    currency: str = Field(default="CNY", max_length=10)
    channel: str = Field(..., min_length=2, max_length=40)
    payment_provider: str = Field(..., min_length=2, max_length=40)
    provider_payment_id: str = Field(..., min_length=4, max_length=200)
    note: str | None = Field(default=None, max_length=500)


@router.get("/ops/survival")
def hermes_platform_survival_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """财迷疯生存基金 — 仅超管；真钱台账 + runway；与租户账单隔离。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.platform_survival_service import survival_status
    return success_response(data=survival_status(db))


class WorldFirstSurvivalBody(BaseModel):
    amount_minor: int = Field(..., ge=1, description="最小货币单位，USD 为分")
    currency: str = Field(default="USD", max_length=10)
    transaction_id: str = Field(..., min_length=4, max_length=200, description="万里汇交易/入账流水号")
    inbound_type: str = Field(default="b2b_tt", max_length=40)
    note: str | None = Field(default=None, max_length=500)


@router.get("/ops/survival/worldfirst/setup")
def hermes_worldfirst_setup_hints(current_user: User = Depends(get_current_user)):
    """万里汇 survival 开户清单（超管）。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.platform_survival_service import worldfirst_setup_hints
    return success_response(data=worldfirst_setup_hints())


@router.post("/ops/survival/worldfirst/record")
def hermes_worldfirst_survival_record(
    body: WorldFirstSurvivalBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """万里汇到账 → 平台 survival 真钱台账（幂等 transaction_id）。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.platform_survival_service import record_worldfirst_inbound
    result = record_worldfirst_inbound(
        db,
        amount_minor=body.amount_minor,
        currency=body.currency,
        transaction_id=body.transaction_id.strip(),
        inbound_type=body.inbound_type,
        note=body.note,
        recorded_by_user_id=str(current_user.id) if current_user else None,
    )
    if not result.get("ok"):
        return success_response(data=result, message=result.get("error") or "record_failed")
    return success_response(data=result, message="万里汇 survival 已入账（真钱）")


@router.post("/ops/survival/worldfirst/webhook")
async def hermes_worldfirst_survival_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    万里汇 Webhook → 平台 survival 自动入账（L6）。
    鉴权：Bearer SURVIVAL_WORLDFIRST_WEBHOOK_SECRET 或 X-WorldFirst-Signature HMAC-SHA256。
    """
    raw = await request.body()
    from app.services.hermes.greedy_avatar_constitution import GreedyAvatarViolation
    from app.services.hermes.worldfirst_webhook_service import handle_worldfirst_webhook
    try:
        result = handle_worldfirst_webhook(
            db,
            raw,
            signature_header=request.headers.get("X-WorldFirst-Signature")
            or request.headers.get("x-worldfirst-signature"),
            authorization_header=request.headers.get("authorization"),
        )
    except GreedyAvatarViolation as exc:
        return error_response(403, str(exc))

    if not result.get("ok"):
        err = str(result.get("error") or "webhook_failed")
        if err in ("webhook_secret_not_configured", "missing_auth_or_signature", "invalid_signature"):
            return success_response(data=result, message=err)
        return success_response(data=result, message=err)
    msg = "万里汇 webhook 已入账"
    if result.get("duplicate"):
        msg = "万里汇 webhook 幂等命中（已入账）"
    return success_response(data=result, message=msg)


class GreedyRevenueLoopRunBody(BaseModel):
    message: str = Field(default="", max_length=2000)
    locale: str = Field(default="global", max_length=20)
    survival_goal_cny: int = Field(default=1000, ge=1)
    max_agency_steps: int | None = Field(default=8, ge=1, le=20)


class GreedyPublishReviewBody(BaseModel):
    queue_index: int = Field(..., ge=0, description="与 GET publish-queue 返回的 queue_index 一致")
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: str | None = Field(default=None, max_length=500)


class GreedyAgencyPlanBody(BaseModel):
    intent: str | None = Field(default=None, max_length=80)
    lane: str | None = Field(default=None, max_length=40)
    message: str = Field(default="", max_length=2000)
    locale: str = Field(default="global", max_length=20)
    survival_goal_cny: int = Field(default=1000, ge=1)


class GreedyAgencyRunBody(GreedyAgencyPlanBody):
    workflow_id: str | None = Field(default=None, max_length=120)
    playbook_id: str | None = Field(default=None, max_length=80)
    max_steps: int | None = Field(default=8, ge=1, le=20)


@router.get("/greedy/hub")
def hermes_greedy_hub(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """摸金校尉总控 — 累计/大赛/耐力/闭环/队列/生存 一次拉取。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_hub_service import greedy_hub_snapshot
    return success_response(data=greedy_hub_snapshot(db))


@router.get("/greedy/readiness")
def hermes_greedy_readiness(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """摸金校尉生产就绪 checklist（上线前核对）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_production_readiness_service import greedy_production_readiness
    return success_response(data=greedy_production_readiness(db))


@router.post("/greedy/ops/bootstrap-tenant")
def hermes_greedy_bootstrap_tenant(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    bootstrap_accounts: bool = Query(True),
):
    """创建 platform-survival.ops 自营租户 + 可选占位 platform_account。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_production_readiness_service import (
        bootstrap_publish_platform_accounts,
        ensure_greedy_publish_tenant,
    )
    tenant = ensure_greedy_publish_tenant(db)
    if not tenant.get("ok"):
        return success_response(data=tenant, message="bootstrap 失败")
    out: dict[str, Any] = {"tenant": tenant}
    if bootstrap_accounts and tenant.get("tenant_id"):
        out["accounts"] = bootstrap_publish_platform_accounts(
            db,
            tenant_id=str(tenant["tenant_id"]),
            locale=str(getattr(settings, "HERMES_GREEDY_DEFAULT_LOCALE", "global") or "global"),
        )
    return success_response(data=out, message="摸金自营租户已 bootstrap")


@router.get("/greedy/publish-queue/tasks")
def hermes_greedy_publish_tasks(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """摸金 L4 审核后创建的 PublishTask 列表。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_survival_publish_service import list_survival_publish_tasks
    return success_response(data=list_survival_publish_tasks(db, limit=limit))


@router.get("/greedy/constitution")
def hermes_greedy_constitution(current_user: User = Depends(get_current_user)):
    """摸金校尉宪法（财迷疯分身；与 SaaS 维护宪法隔离）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_avatar_constitution import greedy_constitution_payload
    return success_response(data=greedy_constitution_payload())


@router.get("/greedy/contest/cumulative")
def hermes_greedy_contest_cumulative(current_user: User = Depends(get_current_user)):
    """全球周/月/年累计 + 打江山人格（比上次更强）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_cumulative_personality_service import get_cumulative_stats
    return success_response(data=get_cumulative_stats())


@router.get("/greedy/contest/endurance")
def hermes_greedy_contest_endurance(current_user: User = Depends(get_current_user)):
    """7×24×30×12 持久耐力赛：当前擂台、倒计时、历史轮次。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_contest_memory_service import get_endurance_status
    from app.services.hermes.greedy_endurance_scheduler import greedy_endurance_scheduler
    data = get_endurance_status()
    data["scheduler_7x24"] = greedy_endurance_scheduler.status()
    return success_response(data=data)


@router.get("/greedy/contest/leaderboard")
def hermes_greedy_contest_leaderboard(
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """挣钱大赛排行榜 — 持续盈利专家 protected / never_offline。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_contest_memory_service import get_contest_leaderboard
    return success_response(data=get_contest_leaderboard(limit=limit))


@router.get("/greedy/contest/project-board")
def hermes_greedy_contest_project_board(
    limit: int = Query(80, ge=10, le=100),
    current_user: User = Depends(get_current_user),
):
    """挣钱项目看板 — SKU 归因收入与完成率（大赛轮次 + L4 审核）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_project_board_service import get_project_earnings_board
    return success_response(data=get_project_earnings_board(leaderboard_limit=limit))


@router.get("/greedy/contest/status")
def hermes_greedy_contest_status(current_user: User = Depends(get_current_user)):
    """大赛季况摘要（Top5 + protected 编制数）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_contest_memory_service import contest_status_summary
    return success_response(data=contest_status_summary())


@router.get("/greedy/memory/mojin")
def hermes_greedy_mojin_memory(current_user: User = Depends(get_current_user)):
    """摸金校尉长期记忆（防失忆）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_contest_memory_service import get_mojin_memory
    return success_response(data=get_mojin_memory())


@router.get("/greedy/memory/roles/{role_id:path}")
def hermes_greedy_role_memory(
    role_id: str,
    current_user: User = Depends(get_current_user),
):
    """单专家经验与大赛 tier（champion 永不下线）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.agency.role_loader import load_role
    from app.services.hermes.greedy_contest_memory_service import get_role_memory
    rid = role_id.strip().strip("/")
    if not load_role(rid):
        return error_response(404, "未找到该专家角色")
    return success_response(data=get_role_memory(rid))


@router.get("/greedy/expert-inspect/{role_id:path}")
def hermes_greedy_expert_inspect(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """专家功能巡检 — 根据专家分类自动执行相关功能检查。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.agency.role_loader import load_role
    from app.services.hermes.expert_inspection_registry import inspect_expert
    rid = role_id.strip().strip("/")
    if not load_role(rid):
        return error_response(404, "未找到该专家角色")
    result = inspect_expert(rid, db)
    from app.models.user import OperationLog
    import json
    log_entry = OperationLog(
        user_id=str(current_user.id),
        action="EXPERT_INSPECTION",
        resource_type="security_event",
        resource_id=rid,
        detail=json.dumps({
            "role_id": rid,
            "category": result.get("category"),
            "inspection_type": result.get("inspection_type"),
            "score": result.get("score"),
            "action_count": len(result.get("next_actions", [])),
        }),
        ip_address="127.0.0.1",
    )
    db.add(log_entry)
    db.commit()
    return success_response(data=result)


@router.get("/greedy/expert-inspect/categories")
def hermes_greedy_expert_inspect_categories(current_user: User = Depends(get_current_user)):
    """巡检分类列表 — 展示所有专家分类及其巡检类型。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.expert_inspection_registry import list_inspection_categories
    return success_response(data=list_inspection_categories())


@router.post("/greedy/expert-execute/{role_id:path}")
def hermes_greedy_expert_execute(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """专家执行专职工作 — 根据专家分类自动执行实际操作。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.agency.role_loader import load_role
    from app.services.hermes.expert_execution_registry import execute_expert
    rid = role_id.strip().strip("/")
    if not load_role(rid):
        return error_response(404, "未找到该专家角色")
    result = execute_expert(rid, db)
    from app.models.user import OperationLog
    import json
    log_entry = OperationLog(
        user_id=str(current_user.id),
        action="EXPERT_EXECUTION",
        resource_type="security_event",
        resource_id=rid,
        detail=json.dumps({
            "role_id": rid,
            "category": result.get("category"),
            "execution_type": result.get("execution_type"),
            "success_count": result.get("success_count"),
            "total_steps": result.get("total_steps"),
            "total_duration_ms": result.get("total_duration_ms"),
        }),
        ip_address="127.0.0.1",
    )
    db.add(log_entry)
    db.commit()
    return success_response(data=result)


@router.get("/greedy/expert-execute/categories")
def hermes_greedy_expert_execute_categories(current_user: User = Depends(get_current_user)):
    """执行分类列表 — 展示所有专家分类及其执行类型。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.expert_execution_registry import list_execution_categories
    return success_response(data=list_execution_categories())


@router.get("/greedy/publish-queue")
def hermes_greedy_publish_queue(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """L4 Redis 发布队列（game/XR SKU staging）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_revenue_loop_service import get_greedy_publish_queue
    return success_response(data=get_greedy_publish_queue(limit=limit))


@router.get("/greedy/publish-queue/history")
def hermes_greedy_publish_queue_history(
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """L4 发布队列审核历史。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_publish_queue_service import get_publish_review_history
    return success_response(data={"history": get_publish_review_history(limit=limit)})


@router.post("/greedy/publish-queue/review")
def hermes_greedy_publish_queue_review(
    body: GreedyPublishReviewBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """人工审核 L4 队列：approve 生成发布计划并记分；reject 移出队列。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_publish_queue_service import review_publish_queue_item
    reviewer = getattr(current_user, "username", None) or str(getattr(current_user, "id", ""))
    result = review_publish_queue_item(
        queue_index=body.queue_index,
        action=body.action,  # type: ignore[arg-type]
        reviewer=reviewer,
        reason=body.reason,
        db=db,
    )
    if not result.get("ok"):
        return success_response(data=result, message=result.get("error") or "审核未通过")
    msg = "已通过并生成发布计划" if body.action == "approve" else "已驳回并移出队列"
    return success_response(data=result, message=msg)


@router.get("/greedy/survival-digest/preview")
def hermes_greedy_survival_digest_preview(current_user: User = Depends(get_current_user)):
    """Survival 周报预览（不发飞书）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_survival_digest_service import build_survival_digest_markdown
    return success_response(data=build_survival_digest_markdown())


@router.post("/greedy/survival-digest/send")
def hermes_greedy_survival_digest_send(current_user: User = Depends(get_current_user)):
    """立即推送 Survival 周报到飞书。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_survival_digest_service import send_survival_digest_feishu
    result = send_survival_digest_feishu(respect_cooldown=False)
    if not result.get("sent"):
        return success_response(data=result, message=result.get("reason") or "飞书发送失败")
    return success_response(data=result, message="Survival 周报已推送飞书")


@router.get("/greedy/survival-digest/scheduler")
def hermes_greedy_survival_digest_scheduler_status(current_user: User = Depends(get_current_user)):
    """Survival 周报调度器状态。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.core.config import settings as cfg
    from app.services.hermes.greedy_survival_digest_scheduler import greedy_survival_digest_scheduler
    st = greedy_survival_digest_scheduler.status()
    st["scheduler_enabled"] = cfg.greedy_survival_digest_scheduler_active
    return success_response(data=st)


@router.get("/greedy/revenue-loop")
def hermes_greedy_revenue_loop_status(current_user: User = Depends(get_current_user)):
    """搞钱闭环 L1–L6 状态与最近快照。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_revenue_loop_service import greedy_revenue_loop_status
    from app.services.hermes.greedy_revenue_loop_scheduler import greedy_revenue_loop_scheduler
    data = greedy_revenue_loop_status()
    data["scheduler"] = greedy_revenue_loop_scheduler.status()
    return success_response(data=data)


@router.post("/greedy/revenue-loop/run")
def hermes_greedy_revenue_loop_run(
    body: GreedyRevenueLoopRunBody,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background: bool = Query(True),
):
    """摸金校尉一整轮：调研→编排→生产→发出→跟踪→收款。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err

    def _bg(payload: GreedyRevenueLoopRunBody) -> None:
        """
        处理 _bg 相关业务逻辑。

        :param payload: 入参 (GreedyRevenueLoopRunBody)。

        :return: 返回 None 类型的结果。
        """
        from app.core.database import SessionLocal
        from app.services.hermes.greedy_revenue_loop_service import run_greedy_revenue_loop
        sdb = SessionLocal()
        try:
            run_greedy_revenue_loop(
                sdb,
                message=payload.message,
                locale=payload.locale,
                survival_goal_cny=payload.survival_goal_cny,
                max_agency_steps=payload.max_agency_steps,
                trigger="hermes_api",
            )
        finally:
            sdb.close()

    if background:
        background_tasks.add_task(_bg, body)
        return success_response(
            data={"status": "started", "mode": "background", "locale": body.locale},
            message="摸金校尉搞钱闭环已在后台启动",
        )

    from app.services.hermes.greedy_revenue_loop_service import run_greedy_revenue_loop
    report = run_greedy_revenue_loop(
        db,
        message=body.message,
        locale=body.locale,
        survival_goal_cny=body.survival_goal_cny,
        max_agency_steps=body.max_agency_steps,
        trigger="hermes_api",
    )
    return success_response(data=report, message="摸金校尉搞钱闭环已完成")


@router.get("/greedy/revenue-loop/scheduler")
def hermes_greedy_revenue_loop_scheduler_status(current_user: User = Depends(get_current_user)):
    """日调度器状态（与 SaaS 巡站调度隔离）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.core.config import settings as cfg
    from app.services.hermes.greedy_revenue_loop_scheduler import greedy_revenue_loop_scheduler
    st = greedy_revenue_loop_scheduler.status()
    st["scheduler_enabled"] = cfg.greedy_revenue_loop_scheduler_active
    return success_response(data=st)


@router.post("/greedy/revenue-loop/cron")
def hermes_greedy_revenue_loop_cron(
    request: Request,
    db: Session = Depends(get_db),
):
    """外部 cron：跑一轮搞钱闭环（OPS_CRON_TOKEN 保护）。"""
    if err := _require_cron(request):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_revenue_loop_scheduler import greedy_revenue_loop_scheduler
    report = greedy_revenue_loop_scheduler.run_once(trigger="cron")
    if report.get("skipped"):
        return success_response(data=report, message="调度跳过（leader lock）")
    return success_response(data={"loop_complete": report.get("loop_complete"), "trigger": "cron"}, message="cron 搞钱闭环已完成")


@router.get("/greedy/agency/status")
def hermes_greedy_agency_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """财迷疯 × agency 专家库编排状态。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_agency_orchestrator_service import greedy_agency_status
    return success_response(data=greedy_agency_status(db))


@router.get("/greedy/agency/roles")
def hermes_greedy_agency_roles(
    category: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    """财迷疯选人用轻量角色目录。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_agency_orchestrator_service import greedy_agency_catalog_summary
    return success_response(data=greedy_agency_catalog_summary(category=category, limit=limit))


@router.post("/greedy/agency/plan")
def hermes_greedy_agency_plan(
    body: GreedyAgencyPlanBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """只读编排计划（不调用 LLM）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.greedy_agency_orchestrator_service import plan_greedy_orchestration
    plan = plan_greedy_orchestration(
        intent=body.intent,
        lane=body.lane,
        message=body.message,
        locale=body.locale,
        survival_goal_cny=body.survival_goal_cny,
        db=db,
    )
    return success_response(data=plan, message="财迷疯编排计划已生成（须人审后执行）")


@router.get("/greedy/agency/roles/{role_id:path}/economics")
def hermes_greedy_role_economics(
    role_id: str,
    current_user: User = Depends(get_current_user),
):
    """单专家变现契约（产什么、哪段 L、如何换算 survival KPI）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.agency.role_loader import load_role
    from app.services.hermes.role_economics_service import resolve_role_economics
    rid = role_id.strip().strip("/")
    if not load_role(rid):
        return error_response(404, "未找到该专家角色")
    return success_response(data=resolve_role_economics(rid))


@router.get("/greedy/agency/economics/publish-skus")
def hermes_greedy_publish_skus(current_user: User = Depends(get_current_user)):
    """L4 发布 SKU 目录（含互动 demo / XR 展示）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.role_economics_service import list_publish_sku_catalog
    return success_response(data=list_publish_sku_catalog())


@router.get("/greedy/agency/economics/coverage")
def hermes_greedy_economics_coverage(current_user: User = Depends(get_current_user)):
    """211 专家变现覆盖率（active/bench/dormant）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.role_economics_service import economics_coverage_report
    return success_response(data=economics_coverage_report())


@router.get("/greedy/agency/economics/rank")
def hermes_greedy_economics_rank(
    intent: str | None = Query(None),
    lane: str | None = Query(None),
    loop_stage: str | None = Query(None),
    limit: int = Query(12, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """按 intent/lane/L 段排序可上场专家（survival_score）。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err
    from app.services.hermes.role_economics_service import rank_roles_for_survival
    rows = rank_roles_for_survival(
        intent=intent,
        lane=lane,
        loop_stage=loop_stage,
        limit=limit,
    )
    return success_response(data={"intent": intent, "lane": lane, "roles": rows})


@router.post("/greedy/agency/run")
def hermes_greedy_agency_run(
    body: GreedyAgencyRunBody,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background: bool = Query(True),
):
    """财迷疯驱动 agency YAML DAG。"""
    if err := _ops_gate(current_user):
        return err
    if err := _greedy_gate():
        return err

    inputs = {
        "locale": body.locale,
        "survival_goal_cny": body.survival_goal_cny,
        "product_context": body.message,
    }
    def _bg(payload: GreedyAgencyRunBody) -> None:
        """
        处理 _bg 相关业务逻辑。

        :param payload: 入参 (GreedyAgencyRunBody)。

        :return: 返回 None 类型的结果。
        """
        from app.core.database import SessionLocal
        from app.services.hermes.greedy_agency_orchestrator_service import run_greedy_orchestration
        sdb = SessionLocal()
        try:
            run_greedy_orchestration(
                sdb,
                workflow_id=payload.workflow_id,
                playbook_id=payload.playbook_id,
                intent=payload.intent,
                inputs={
                    "locale": payload.locale,
                    "survival_goal_cny": payload.survival_goal_cny,
                    "product_context": payload.message,
                },
                max_steps=payload.max_steps,
            )
        finally:
            sdb.close()

    if background:
        background_tasks.add_task(_bg, body)
        return success_response(
            data={"status": "started", "mode": "background", "intent": body.intent},
            message="财迷疯 agency 编排已在后台启动",
        )

    from app.services.hermes.greedy_agency_orchestrator_service import run_greedy_orchestration
    result = run_greedy_orchestration(
        db,
        workflow_id=body.workflow_id,
        playbook_id=body.playbook_id,
        intent=body.intent,
        inputs=inputs,
        max_steps=body.max_steps,
    )
    return success_response(data=result, message="财迷疯 agency 编排已完成")


@router.post("/ops/survival/record")
def hermes_platform_survival_record(
    body: SurvivalRecordBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    超管确认入账（通用通道；万里汇请优先 POST .../worldfirst/record）。
    必须 provider_payment_id；入账 platform_survival 钱包，不进租户/代理分润。
    """
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.platform_survival_service import record_survival_settlement
    result = record_survival_settlement(
        db,
        amount_minor=body.amount_minor,
        currency=body.currency,
        channel=body.channel,
        payment_provider=body.payment_provider,
        provider_payment_id=body.provider_payment_id,
        recorded_by_user_id=str(current_user.id) if current_user else None,
        note=body.note,
    )
    if not result.get("ok"):
        return success_response(data=result, message=result.get("error") or "record_failed")
    return success_response(data=result, message="平台生存基金已入账（真钱）")


@router.post("/ops/instruct")
def hermes_ops_instruct(
    body: OpsInstructBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """人工跟进指令（飞书/Admin 等价）：巡站、技术雷达、全套、确认告警。"""
    if err := _ops_gate(current_user):
        return err
    from app.services.hermes.safe_remediation import execute_human_instruction
    outcome = execute_human_instruction(db, body.command.strip())
    if outcome.get("error"):
        return success_response(data=outcome, message=outcome["error"])
    return success_response(data=outcome, message=f"已执行指令: {body.command.strip()}")


@router.get("/tickets/{ticket_id}")
def hermes_ticket_detail(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ticket_id 即 pipeline_run_id 或 insight_id。"""
    from app.models.ubrain_commercial_os import UbrainPipelineRun, UbrainResearchInsight
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")

    pipe = (
        db.query(UbrainPipelineRun)
        .filter(
            UbrainPipelineRun.id == ticket_id,
            UbrainPipelineRun.tenant_id == tenant_id,
        )
        .first()
    )
    if pipe:
        import json
        return success_response(
            data=sanitize_public_data(
                {
                    "ticket_id": pipe.id,
                    "type": "pipeline",
                    "status": pipe.status,
                    "steps": json.loads(pipe.steps_json or "[]"),
                    "created_job_ids": json.loads(pipe.created_job_ids_json or "[]"),
                    "finished_at": pipe.finished_at.isoformat() if pipe.finished_at else None,
                }
            )
        )
    insight = (
        db.query(UbrainResearchInsight)
        .filter(
            UbrainResearchInsight.id == ticket_id,
            UbrainResearchInsight.tenant_id == tenant_id,
        )
        .first()
    )
    if insight:
        return success_response(
            data=sanitize_public_data(
                {
                    "ticket_id": insight.id,
                    "type": "insight",
                    "title": insight.title,
                    "summary": insight.summary,
                    "intent": insight.intent,
                    "created_at": insight.created_at.isoformat() if insight.created_at else None,
                }
            )
        )
    return error_response(404, "未找到该工单")
