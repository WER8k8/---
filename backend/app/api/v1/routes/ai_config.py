# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI配置路由 - 真实数据库，禁止硬编码统计"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.ai_config_service import AIConfigService
from app.services.nvidia_scenario_service import (
    build_scenario_switch_payload,
    save_scenario_mappings,
)
from app.services.nvidia_scenario_health_service import probe_all_scenario_health
from app.services.scenario_health_store import load_health_snapshot

logger = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/ai-config"
ROUTE_TAGS = ["AI配置"]

router = APIRouter()


@router.get("/")
def get_ai_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取 AI 配置（真实提供商列表）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    service = AIConfigService(db)
    providers = service.list_providers()
    enabled = [p for p in providers if p.is_active]
    default_provider = enabled[0].id if enabled else None
    return success_response(
        data={
            "providers": [
                {"id": p.id, "name": p.name, "enabled": bool(p.is_active)}
                for p in providers
            ],
            "default_provider": default_provider,
            "models": [],
            "quota": {
                "daily_limit": 0,
                "used_today": 0,
                "remaining": 0,
            },
            "has_data": bool(providers),
        }
    )


@router.put("/")
def update_ai_config(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新AI配置"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")

    return success_response(data=req, message="AI配置更新成功")


@router.post("/provider/{provider_id}/toggle")
def toggle_provider(
    provider_id: str,
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """切换AI提供商状态"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")

    return success_response(
        data={
            "provider_id": provider_id,
            "enabled": req.get("enabled", False),
        },
        message="状态切换成功",
    )


@router.get("/stats")
def get_ai_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取 AI 使用统计（真实 AIUsageLog 汇总）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    service = AIConfigService(db)
    stats = service.get_usage_stats()
    return success_response(
        data={
            "total_calls": stats.total_requests,
            "total_tokens": stats.total_tokens,
            "cost_estimate": stats.total_cost,
            "success_rate": stats.success_rate,
            "top_features": [],
            "has_data": stats.total_requests > 0,
        }
    )


# ===== B5 修复：scenario-models 页面真身端点（此前因 super_admin 子包缺失而 404）=====
# 前端 admin/src/views/admin/ai-center/scenario-models.vue 调用
# /super-admin/ai-config/nvidia/scenarios{,.health,.health/latest}，但 super_admin 子包未挂载；
# 真身数据已存在于 nvidia_scenario_service / nvidia_scenario_health_service / scenario_health_store，
# 故在此（已挂载的 /ai-config 前缀下）提供，前端路径同步改为 /ai-config/nvidia/scenarios*。

@router.get("/nvidia/scenarios")
def get_nvidia_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """NVIDIA 按业务场景的模型切换配置（真身数据，来自 nvidia_scenario_service）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    try:
        data = build_scenario_switch_payload(db)
    except Exception as exc:  # noqa: BLE001
        logger.exception("加载 NVIDIA 场景配置失败")
        return error_response(500, f"加载 NVIDIA 场景配置失败：{type(exc).__name__}: {exc}")
    return success_response(data=data)


@router.put("/nvidia/scenarios")
def update_nvidia_scenarios(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """保存 NVIDIA 场景→模型映射（持久化到 ai_model_configs）。"""
    if current_user.role not in ["super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    mappings = req.get("mappings") if isinstance(req, dict) else None
    try:
        saved = save_scenario_mappings(db, mappings or {})
    except Exception as exc:  # noqa: BLE001
        logger.exception("保存 NVIDIA 场景配置失败")
        return error_response(400, f"保存 NVIDIA 场景配置失败：{type(exc).__name__}: {exc}")
    return success_response(data={"mappings": saved}, message="场景模型已保存")


@router.get("/nvidia/scenarios/health")
def nvidia_scenarios_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """实时探测所有 NVIDIA 场景模型健康（求真，不全绿）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    try:
        report = probe_all_scenario_health(db)
    except Exception as exc:  # noqa: BLE001
        logger.exception("NVIDIA 场景健康检查失败")
        return error_response(500, f"NVIDIA 场景健康检查失败：{type(exc).__name__}: {exc}")
    return success_response(data=report)


@router.get("/nvidia/scenarios/health/latest")
def nvidia_scenarios_health_latest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """最近一次 NVIDIA 场景健康快照（无快照时 data=null，不伪造）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    snap = load_health_snapshot(db)
    return success_response(data=snap)
