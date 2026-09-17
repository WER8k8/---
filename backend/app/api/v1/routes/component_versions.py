# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""组件版本管理 API。"""
import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.services.component_version_manager import ComponentVersionManager

router = APIRouter(prefix="/component-versions", tags=["component-versions"])

_MODULE_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$")
_ALLOWED_MODULES = {
    "app.services.hermes.planner_service",
    "app.services.hermes.task_control_supervisor",
    "app.services.hermes.experience_engine",
    "app.services.deepseek_harness.client",
    "app.services.component_version_manager",
    "app.services.boq_calculator",
    "app.services.saas_billing",
    "app.services.lead_enrichment",
    "app.services.content_adapter",
    "app.services.whatsapp_bridge",
}


class RegisterRequest(BaseModel):
    module: str
    version: str
    hash: str = ""

    @field_validator("module")
    @classmethod
    def validate_module(cls, v: str) -> str:
        if len(v) > 200 or not _MODULE_RE.match(v):
            raise ValueError("Invalid module name")
        return v


class RollbackRequest(BaseModel):
    module: str
    target_version: str | None = None

    @field_validator("module")
    @classmethod
    def validate_module(cls, v: str) -> str:
        if len(v) > 200 or not _MODULE_RE.match(v):
            raise ValueError("Invalid module name")
        return v


def _check_module_allowed(module: str):
    if module not in _ALLOWED_MODULES:
        raise HTTPException(403, f"Module {module} not in allowed list")


@router.get("")
def list_components(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出所有组件当前版本。"""
    return {m: {"version": v.version, "status": v.status, "loaded_at": v.loaded_at}
            for m, v in ComponentVersionManager.list_all().items() if v}


@router.get("/{module}/history")
def component_history(
    module: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查看组件版本历史。"""
    _check_module_allowed(module)
    return [{"version": v.version, "status": v.status, "loaded_at": v.loaded_at, "hash": v.hash}
            for v in ComponentVersionManager.history(module)]


@router.post("/register")
def register_component(
    req: RegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """注册组件版本。"""
    _check_module_allowed(req.module)
    cv = ComponentVersionManager.register(req.module, req.version, req.hash)
    return {"module": cv.module, "version": cv.version, "status": cv.status}


@router.post("/hot-reload")
def hot_reload(
    module: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """热更新组件（仅管理员）。"""
    _check_module_allowed(module)
    ok = ComponentVersionManager.hot_reload(module)
    if not ok:
        raise HTTPException(400, f"Hot-reload failed for {module}")
    return {"module": module, "status": "reloaded"}


@router.post("/rollback")
def rollback(
    req: RollbackRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """回滚组件到指定版本（仅管理员）。"""
    _check_module_allowed(req.module)
    ok = ComponentVersionManager.rollback(req.module, req.target_version)
    if not ok:
        raise HTTPException(400, f"Rollback failed for {req.module}")
    return {"module": req.module, "status": "rolled-back"}
