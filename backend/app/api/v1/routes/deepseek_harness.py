# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DeepSeek Harness 外层运行时接入路由（总纲 §外层 / 轮次续接）。

把 dsh 作为"外层编排大脑"暴露给后端：
- GET  /deepseek-harness/health : 运行时可用性（SDK 是否安装 / 二进制是否存在 / 配置）
- POST /deepseek-harness/invoke : 跑一次 dsh 外层 agent turn，返回 final_response

协同：hermes_task_bridge 已注册 task_type="deepseek_harness"，因此统一编排入口
/orchestration/tasks 也能把外层请求路由到 dsh（外层 → Hermes 内层 的拓扑成立）。

注：SDK 在本文件内懒加载，未安装时 health 正常返回 available=false，不影响其他路由挂载。
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_user
from app.models.user import User

logger = get_logger(__name__)

ROUTE_PREFIX = "/deepseek-harness"
ROUTE_TAGS = ["DeepSeek Harness 外层"]

router = APIRouter(prefix="", tags=["DeepSeek Harness 外层"])


class InvokeRequest(BaseModel):
    prompt: str = Field(..., description="交给 dsh 外层智能体的任务 / 提示词")
    session_id: Optional[str] = Field(None, description="会话 ID，复用可续接上下文")
    profile: Optional[str] = Field(None, description="dsh profile，默认 sdk-minimal")
    provider: Optional[str] = Field(None, description="provider 路由，默认 deepseek-official")
    model: Optional[str] = Field(None, description="模型 id，默认 deepseek-v4-flash")
    reasoning_effort: Optional[str] = Field(None, description="可选推理强度标识")
    max_tokens: Optional[int] = Field(None, description="可选单次输出 token 上限")


class InvokeResponse(BaseModel):
    session_id: str
    final_response: str
    finish_reason: Optional[str] = None
    event_count: int = 0
    provider: str
    model: str
    profile: str


class HealthResponse(BaseModel):
    """公共探活字段：不暴露内部路径 / API Key 存在性 / LLM base_url。"""
    available: bool
    sdk_importable: bool
    enabled: bool


@router.get("/health", response_model=HealthResponse)
def health() -> dict:
    """dsh 运行时可用性探测（无需鉴权也可访问，便于运维探活；仅返回公共状态）。"""
    from app.services.deepseek_harness.client import health as _health

    raw = _health()
    return {
        "available": bool(raw.get("available")),
        "sdk_importable": bool(raw.get("sdk_importable")),
        "enabled": bool(raw.get("enabled")),
    }


@router.post("/invoke", response_model=InvokeResponse)
def invoke(
    req: InvokeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InvokeResponse:
    """跑一次 dsh 外层 agent turn。需登录。prompt 为空会被拒。"""
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt_required")
    from app.services.deepseek_harness.client import run_turn

    try:
        result = run_turn(
            req.prompt.strip(),
            session_id=req.session_id,
            profile=req.profile,
            provider=req.provider,
            model=req.model,
            reasoning_effort=req.reasoning_effort,
            max_tokens=req.max_tokens,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("deepseek-harness invoke 失败")
        raise HTTPException(status_code=502, detail=f"deepseek_harness_error: {exc}")
    return InvokeResponse(**result)
