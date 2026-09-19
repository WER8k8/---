# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一编排摄入 API（对接总纲 §4.6 统一任务面）。

把"外部请求 / 上传事件 / n8n 入站"等统一接入 ai_tasks，再派发 Hermes 编排：
- POST /orchestration/tasks   : 创建任务 + 立即入 Celery 执行（默认）
- GET  /orchestration/tasks/{id}: 查询任务状态/结果

关键：所有编排场景只经此一个入口进 ai_tasks，不直接摸 DeerFlow/n8n；调度主权归
Control Plane。加场景只需在 hermes_task_bridge.ROUTERS 注册 task_type，不动本路由。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_user
from app.models.tenant import UserTenant
from app.models.user import User
from app.schemas.hermes_orchestration import IntentEvent
from app.services.tasks.task_control import TaskControlService
from app.services.registry.skill_service import seed_default_skills
from app.tasks.orchestration_tasks import process_ai_task

logger = get_logger(__name__)

ROUTE_PREFIX = "/orchestration"
ROUTE_TAGS = ["统一编排摄入"]

router = APIRouter(prefix="", tags=["统一编排摄入"])


class OrchestrationTaskRequest(BaseModel):
    task_type: str = Field(..., description="任务类型，如 ai_site_build / ubrain_intent")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="任务输入（product_name / message / product_images 等）")
    tenant_id: Optional[str] = Field(None, description="超管可显式指定租户；普通用户自动解析")
    idempotency_key: Optional[str] = Field(None, description="幂等键，(tenant,key) 重复提交返回已有任务")
    priority: int = Field(5, description="优先级 1-10")
    auto_dispatch: bool = Field(True, description="创建后立即入 Celery 执行")


class OrchestrationTaskResponse(BaseModel):
    task_id: str
    status: str
    detail: str = ""


def _resolve_tenant_id(
    db: Session, current_user: User, tenant_id: Optional[str] = None
) -> str:
    """解析当前用户关联的租户 ID。超级管理员可显式指定租户，普通用户自动解析。"""
    if tenant_id:
        if getattr(current_user, "is_superuser", False) or getattr(current_user, "role", "") == "super_admin":
            return str(tenant_id)
    link = (
        db.query(UserTenant)
        .filter(UserTenant.user_id == current_user.id, UserTenant.is_active == True)  # noqa: E712
        .first()
    )
    if not link:
        raise HTTPException(status_code=400, detail="用户未关联任何租户")
    return str(link.tenant_id)


class OrchestrationWebhookRequest(BaseModel):
    """n8n / 外部系统入站意图（补 HarnessGateway 入口断点）。"""
    tenant_id: str = Field(..., description="租户 ID")
    text: Optional[str] = Field(None, description="自由文本意图")
    intent: Optional[str] = Field(None, description="结构化高层意图（二选一：text / intent）")
    channel: Optional[str] = Field("n8n", description="触发渠道")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文（语言/配额提示等）")
    payload: Optional[Dict[str, Any]] = Field(None, description="业务参数")


@router.post("/tasks", response_model=OrchestrationTaskResponse)
def create_orchestration_task(
    req: OrchestrationTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrchestrationTaskResponse:
    """创建编排任务并（默认）立即派发执行。"""
    tenant_id = _resolve_tenant_id(db, current_user, req.tenant_id)
    # best-effort：确保 ECC 注册表有真实 Skill 内容（幂等，失败不影响建任务）
    try:
        seed_default_skills(db)
    except Exception as exc:  # noqa: BLE001
        logger.warning("orchestration: seed_default_skills 失败（已忽略）: %s", exc)
    ctl = TaskControlService(db)
    task = ctl.create_task(
        tenant_id=tenant_id,
        task_type=req.task_type,
        input_data=req.input_data,
        idempotency_key=req.idempotency_key,
        priority=req.priority,
        source="orchestration_api",
    )
    if req.auto_dispatch:
        process_ai_task.delay(str(task.id))
    return OrchestrationTaskResponse(
        task_id=str(task.id), status=task.status, detail="已派发执行"
    )


class OrchestrationFromIntentRequest(BaseModel):
    """自然语言意图 → 自动拆解成任务图（走 planner_service.decompose）。"""

    intent: str = Field(..., description="意图描述，如「帮我建站」/「找德国买家并写开发信」")
    payload: Dict[str, Any] = Field(default_factory=dict, description="业务参数（product_name / topic / keyword 等）")
    channel: str = Field("api", description="触发渠道（api / web / n8n / heartbeat）")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文（语言 / 预算提示等）")
    tenant_id: Optional[str] = Field(None, description="超管可显式指定租户")
    auto_dispatch: bool = Field(True, description="拆解后立即派发就绪节点")


class OrchestrationFromIntentResponse(BaseModel):
    plan_id: str
    graph_source: str = Field(..., description="L1_template / L2_llm / L3_minimal")
    node_count: int
    node_tasks: list[str] = Field(default_factory=list, description="子任务 ID 列表")
    dispatched: bool = False


@router.post("/tasks/from-intent", response_model=OrchestrationFromIntentResponse)
async def create_task_from_intent(
    req: OrchestrationFromIntentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrchestrationFromIntentResponse:
    """把一个自然语言意图拆成任务图并入库派发。

    链路：IntentEvent → planner_service.decompose() → parse_graph_to_tasks() → advance_plan()
    decompose 内部有三道安全阀（执行器白名单 / 拓扑治理 / 能力白名单），
    不过阀即降级，绝不出引用不存在执行器的假图。
    """
    import uuid as _uuid

    from app.services.hermes.planner_service import decompose
    from app.services.hermes.task_control_supervisor import (
        advance_plan,
        parse_graph_to_tasks,
    )

    tenant_id = _resolve_tenant_id(db, current_user, req.tenant_id)

    # best-effort：确保技能注册表有内容（幂等，失败不影响）
    try:
        seed_default_skills(db)
    except Exception as exc:  # noqa: BLE001
        logger.warning("from-intent: seed_default_skills 失败（已忽略）: %s", exc)

    event = IntentEvent(
        event_id=f"evt_{_uuid.uuid4().hex[:12]}",
        tenant_id=tenant_id,
        channel=req.channel,
        intent=req.intent,
        payload=req.payload,
        context=req.context,
    )

    try:
        graph, source = await decompose(event, db)
    except Exception as exc:  # noqa: BLE001 — 拆解失败如实报错，不返回假图
        logger.exception("from-intent: 拆解失败 tenant=%s", tenant_id)
        raise HTTPException(status_code=422, detail=f"意图拆解失败: {exc}") from exc

    try:
        node_tasks = parse_graph_to_tasks(db, tenant_id, graph)
    except Exception as exc:  # noqa: BLE001
        logger.exception("from-intent: 任务图落库失败 plan=%s", graph.plan_id)
        raise HTTPException(status_code=500, detail=f"任务图落库失败: {exc}") from exc

    plan_task_id = str(getattr(node_tasks[0], "parent_task_id", "")) if node_tasks else ""

    dispatched = False
    if req.auto_dispatch and plan_task_id:
        try:
            advance_plan(db, plan_task_id)
            dispatched = True
        except Exception as exc:  # noqa: BLE001 — 派发失败不掩盖入库成功
            logger.warning("from-intent: advance_plan 派发失败 plan=%s: %s", plan_task_id, exc)

    return OrchestrationFromIntentResponse(
        plan_id=graph.plan_id,
        graph_source=source,
        node_count=len(graph.nodes),
        node_tasks=[str(t.id) for t in node_tasks],
        dispatched=dispatched,
    )


@router.post("/golden-path/fulfillment", response_model=OrchestrationFromIntentResponse)
async def golden_path_fulfillment(
    req: OrchestrationFromIntentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrchestrationFromIntentResponse:
    """GP-A 一键履约/PI：优丁功能域按钮 → Hermes L1（无附属特权路径）。

    链路与 from-intent 相同，但强制业务意图锚点，便于前端/门禁验收：
    intent 拼入 fulfillment 锚词 → planner L1 `_fulfillment_graph`。
    未配置 GoodJob 桥时执行器诚实 failed，不造假单证。
    """
    base = (req.intent or "").strip()
    if not base:
        base = "履约推进与形式发票"
    req.intent = f"{base} 履约 fulfillment PI 订单跟单"
    req.channel = req.channel or "api"
    ctx = dict(req.context or {})
    ctx.setdefault("golden_path", "GP-A")
    ctx.setdefault("plane", "task")
    req.context = ctx
    return await create_task_from_intent(req, db=db, current_user=current_user)


class GoldenPathOutreachRequest(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict)
    channel: str = Field("api")
    context: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = Field(None)
    auto_dispatch: bool = Field(True)
    intent: str = Field("社媒拓客 WhatsApp 私域触达 prospect social_outreach")


@router.post("/golden-path/outreach", response_model=OrchestrationFromIntentResponse)
async def golden_path_outreach(
    req: GoldenPathOutreachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrchestrationFromIntentResponse:
    """GP-B 社媒拓客：功能域「社媒拓客」→ Hermes L1 trade_ai_agent（无特权）。"""
    inner = OrchestrationFromIntentRequest(
        intent=req.intent,
        payload=req.payload,
        channel=req.channel,
        context={**(req.context or {}), "golden_path": "GP-B", "plane": "task"},
        tenant_id=req.tenant_id,
        auto_dispatch=req.auto_dispatch,
    )
    return await create_task_from_intent(inner, db=db, current_user=current_user)


@router.get("/golden-path/work-mode")
def golden_path_work_mode(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """功能域工作模式契约快照（双平面 / 无特权菜单 / GP-A·B）供前端与门禁。"""
    from app.services.hermes.annex_work_mode import work_mode_report

    return work_mode_report()


@router.get("/tasks/{task_id}", response_model=OrchestrationTaskResponse)
def get_orchestration_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrchestrationTaskResponse:
    """查询编排任务当前状态与结果。"""
    ctl = TaskControlService(db)
    task = ctl.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task_not_found")
    return OrchestrationTaskResponse(task_id=str(task.id), status=task.status)


@router.post("/webhook/intent", response_model=OrchestrationFromIntentResponse)
async def ingest_webhook_intent(
    req: OrchestrationWebhookRequest,
    db: Session = Depends(get_db),
) -> OrchestrationFromIntentResponse:
    """n8n / 外部 webhook 入站 → HarnessGateway 归一化→拆解→返回计划（不自动派发）。"""
    from app.services.hermes.harness_gateway import process_inbound_webhook
    result = await process_inbound_webhook(db, req.model_dump())
    return OrchestrationFromIntentResponse(
        plan_id=result["plan_id"],
        graph_source=result["graph_source"],
        node_count=result["node_count"],
    )
