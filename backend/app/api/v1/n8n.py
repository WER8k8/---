"""n8n 集成 API 路由。

提供 n8n 工作流管理、Webhook 接收、触发调用三大类接口：

Webhook 接收（n8n 回调）:
- POST /api/v1/n8n/webhook/{workflow_id}  — 接收 n8n 回调

工作流管理:
- POST   /api/v1/n8n/workflows            — 注册工作流
- GET    /api/v1/n8n/workflows            — 列出所有工作流
- GET    /api/v1/n8n/workflows/{wf_id}    — 获取工作流详情
- PUT    /api/v1/n8n/workflows/{wf_id}    — 更新工作流
- DELETE /api/v1/n8n/workflows/{wf_id}    — 注销工作流
- PATCH  /api/v1/n8n/workflows/{wf_id}/toggle — 启用/禁用

触发调用:
- POST   /api/v1/n8n/trigger/{wf_id}      — 触发工作流（同步）
- POST   /api/v1/n8n/trigger-async/{wf_id} — 触发工作流（Celery 异步）

统计:
- GET    /api/v1/n8n/stats                 — 注册表统计
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.core.response import success_response
from app.services.n8n.trigger import N8nTriggerService, trigger_n8n_workflow
from app.services.n8n.webhook import N8nWebhookService, verify_webhook_signature
from app.services.n8n.workflow_registry import (
    WorkflowRecord,
    get_workflow_registry,
)

log = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/n8n", tags=["n8n集成"])

# 服务实例
_trigger_service = N8nTriggerService()
_webhook_service = N8nWebhookService()


# ============================================================
# Pydantic 请求/响应模型
# ============================================================

class WorkflowRegisterRequest(BaseModel):
    """工作流注册请求。"""
    workflow_id: str = Field(..., description="n8n 工作流 ID", min_length=1, max_length=128)
    name: str = Field(..., description="工作流名称", min_length=1, max_length=256)
    endpoint: str = Field(..., description="n8n Webhook URL")
    auth_config: dict[str, Any] = Field(default_factory=dict, description="认证配置")
    description: str = Field(default="", description="工作流描述")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    trigger_scene: str = Field(
        default="custom",
        description="触发场景：product_create / content_publish / lead_created / custom",
    )


class WorkflowUpdateRequest(BaseModel):
    """工作流更新请求。"""
    name: Optional[str] = None
    endpoint: Optional[str] = None
    auth_config: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    trigger_scene: Optional[str] = None


class WorkflowTriggerRequest(BaseModel):
    """工作流触发请求。"""
    payload: dict[str, Any] = Field(default_factory=dict, description="发送给 n8n 的 JSON 数据")
    headers: Optional[dict[str, str]] = Field(default=None, description="额外请求头")


class WorkflowToggleRequest(BaseModel):
    """启用/禁用请求。"""
    enabled: bool = Field(..., description="是否启用")


# ============================================================
# Webhook 接收端点（n8n 回调）
# ============================================================

@router.post("/webhook/{workflow_id}", tags=["n8n-webhook"])
async def receive_n8n_webhook(
    workflow_id: str,
    request: Request,
) -> dict[str, Any]:
    """接收 n8n Webhook 回调。

    n8n 工作流执行完成后，通过此端点回调后端系统。
    支持 HMAC-SHA256 签名验证（需在工作流注册时配置 secret）。

    请求头:
        X-N8n-Signature: HMAC-SHA256 签名（可选，需配置 secret）

    请求体:
        JSON 格式，需包含 event_type 或 event 字段标识事件类型。

    典型场景:
        - 自动建站完成 → event_type=site_built
        - 内容分发完成 → event_type=content_distributed
        - Lead 通知完成 → event_type=lead_notified
    """
    # 读取原始请求体
    raw_body = await request.body()
    # 获取签名
    signature = request.headers.get("X-N8n-Signature", "")
    # 查找工作流配置获取 secret
    registry = get_workflow_registry()
    record = registry.get(workflow_id)
    secret = ""
    if record and record.auth_config:
        secret = record.auth_config.get("webhook_secret", "")

    try:
        result = await _webhook_service.handle_webhook(
            workflow_id=workflow_id,
            payload=raw_body,
            signature=signature,
            secret=secret,
            skip_signature_verify=not secret,  # 未配置 secret 则跳过验证
        )
        return success_response(data=result, message="Webhook 处理成功")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# 工作流管理端点
# ============================================================

@router.post("/workflows", tags=["n8n-workflow"])
async def register_workflow(
    body: WorkflowRegisterRequest,
) -> dict[str, Any]:
    """注册 n8n 工作流。

    注册后可通过 trigger 端点触发该工作流。
    """
    registry = get_workflow_registry()
    try:
        record = registry.register(WorkflowRecord(
            workflow_id=body.workflow_id,
            name=body.name,
            endpoint=body.endpoint,
            auth_config=body.auth_config,
            description=body.description,
            tags=body.tags,
            trigger_scene=body.trigger_scene,
        ))
        return success_response(
            data=_record_to_dict(record),
            message="工作流注册成功",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get("/workflows", tags=["n8n-workflow"])
async def list_workflows(
    scene: Optional[str] = Query(None, description="按触发场景过滤"),
    enabled_only: bool = Query(False, description="仅显示启用的工作流"),
):
    """列出所有已注册的 n8n 工作流。"""
    registry = get_workflow_registry()
    if scene:
        records = registry.list_by_scene(scene)
    elif enabled_only:
        records = registry.list_enabled()
    else:
        records = registry.list_all()

    return success_response(
        data=[_record_to_dict(r) for r in records],
        total=len(records),
    )


@router.get("/workflows/{workflow_id}", tags=["n8n-workflow"])
async def get_workflow(
    workflow_id: str,
) -> dict[str, Any]:
    """获取工作流详情。"""
    registry = get_workflow_registry()
    record = registry.get(workflow_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流 {workflow_id} 不存在",
        )
    return success_response(data=_record_to_dict(record))


@router.put("/workflows/{workflow_id}", tags=["n8n-workflow"])
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdateRequest,
) -> dict[str, Any]:
    """更新工作流配置。"""
    registry = get_workflow_registry()
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无更新字段",
        )
    record = registry.update(workflow_id, **update_data)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流 {workflow_id} 不存在",
        )
    return success_response(data=_record_to_dict(record), message="工作流更新成功")


@router.delete("/workflows/{workflow_id}", tags=["n8n-workflow"])
async def unregister_workflow(
    workflow_id: str,
) -> dict[str, Any]:
    """注销工作流。"""
    registry = get_workflow_registry()
    if registry.unregister(workflow_id):
        return success_response(message="工作流注销成功")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"工作流 {workflow_id} 不存在",
    )


@router.patch("/workflows/{workflow_id}/toggle", tags=["n8n-workflow"])
async def toggle_workflow(
    workflow_id: str,
    body: WorkflowToggleRequest,
) -> dict[str, Any]:
    """启用/禁用工作流。"""
    registry = get_workflow_registry()
    record = registry.set_enabled(workflow_id, body.enabled)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流 {workflow_id} 不存在",
        )
    status_text = "启用" if body.enabled else "禁用"
    return success_response(
        data=_record_to_dict(record),
        message=f"工作流已{status_text}",
    )


# ============================================================
# 触发调用端点
# ============================================================

@router.post("/trigger/{workflow_id}", tags=["n8n-trigger"])
async def trigger_workflow(
    workflow_id: str,
    body: WorkflowTriggerRequest,
) -> dict[str, Any]:
    """同步触发 n8n 工作流。

    直接发送 HTTP 请求到 n8n webhook endpoint，等待响应后返回。
    适用于需要立即确认触发结果的场景。
    """
    try:
        result = await _trigger_service.trigger(
            workflow_id=workflow_id,
            payload=body.payload,
            headers=body.headers,
        )
        if result["success"]:
            return success_response(data=result, message="工作流触发成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=result,
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post("/trigger-async/{workflow_id}", tags=["n8n-trigger"])
async def trigger_workflow_async(
    workflow_id: str,
    body: WorkflowTriggerRequest,
) -> dict[str, Any]:
    """异步触发 n8n 工作流（Celery）。

    将触发任务提交到 Celery 队列，立即返回 task_id。
    适用于不需要立即确认结果的场景（如批量分发、异步建站等）。
    """
    registry = get_workflow_registry()
    record = registry.get(workflow_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流 {workflow_id} 未注册",
        )
    if not record.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"工作流 {workflow_id} 已禁用",
        )

    # 提交 Celery 异步任务
    task = trigger_n8n_workflow.delay(
        workflow_id=workflow_id,
        payload=body.payload,
        headers=body.headers,
    )
    return success_response(
        data={
            "task_id": task.id,
            "workflow_id": workflow_id,
            "status": "queued",
        },
        message="触发任务已提交到队列",
    )


# ============================================================
# 统计端点
# ============================================================

@router.get("/stats", tags=["n8n-stats"])
async def get_n8n_stats() -> Any:
    """获取 n8n 集成统计信息。"""
    registry = get_workflow_registry()
    stats = registry.get_stats()
    return success_response(data=stats)


# ============================================================
# 工具函数
# ============================================================

def _record_to_dict(record: WorkflowRecord) -> dict[str, Any]:
    """将 WorkflowRecord 转换为字典。"""
    return {
        "id": record.id,
        "workflow_id": record.workflow_id,
        "name": record.name,
        "endpoint": record.endpoint,
        "auth_config": record.auth_config,
        "enabled": record.enabled,
        "description": record.description,
        "tags": record.tags,
        "trigger_scene": record.trigger_scene,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        "last_triggered_at": record.last_triggered_at.isoformat() if record.last_triggered_at else None,
        "trigger_count": record.trigger_count,
        "success_count": record.success_count,
        "fail_count": record.fail_count,
    }
