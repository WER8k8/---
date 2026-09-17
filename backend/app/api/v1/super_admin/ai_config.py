# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI 模型配置管理接口"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.cache import invalidate_ai_model_cache
from app.core.database import get_db
from app.core.response import success_response
from app.models.ai_config import AIModelConfig, AIModelProvider
from app.models.user import User
from app.services.nvidia_catalog_service import build_nvidia_catalog
from app.services.nvidia_scenario_service import (
    build_scenario_switch_payload,
    save_scenario_mappings,
)
from app.services.nvidia_scenario_health_service import (
    probe_all_scenario_health,
    probe_scenario_health,
)
from app.services.ai_model_capability_service import (
    build_models_enriched_list,
    probe_all_configured_models,
)
from app.services.scenario_health_store import load_health_snapshot
from app.services.scenario_health_scheduler import run_scenario_health_check

router = APIRouter()


class AIProviderCreate(BaseModel):
    name: str
    provider_type: str
    api_key: str
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    is_active: bool = True
    enabled: Optional[bool] = None  # 前端别名
    is_default: bool = False


class AIProviderPatch(BaseModel):
    name: Optional[str] = None
    provider_type: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    is_active: Optional[bool] = None
    enabled: Optional[bool] = None  # 前端别名
    is_default: Optional[bool] = None


class AIModelCreate(BaseModel):
    provider_id: str
    model_name: str
    model_type: str
    temperature: str = "0.7"
    max_tokens: str = "4096"
    is_active: bool = True
    active: Optional[bool] = None  # 前端别名
    is_default: bool = False
    sort_order: Optional[int] = None


class AIModelPatch(BaseModel):
    model_name: Optional[str] = None
    model_type: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[str] = None
    is_active: Optional[bool] = None
    active: Optional[bool] = None  # 前端别名
    is_default: Optional[bool] = None
    sort_order: Optional[int] = None


def _has_api_key(key: Optional[str]) -> bool:
    """_has_api_key。

    参数说明：
    :param key: 参数 key
    :return: 返回处理结果。
    """
    text = (key or "").strip()
    return bool(text) and text not in {"your_", "change-me", "sk-your-key-here"}


def _serialize_provider(p: AIModelProvider, models: list[dict] | None = None) -> dict:
    """_serialize_provider。

    参数说明：
    :param p: 参数 p
    :param models: 参数 models
    :return: 返回处理结果。
    """
    masked = _mask_key(p.api_key) if _has_api_key(p.api_key) else None
    return {
        "id": str(p.id),
        "name": p.name,
        "provider_type": p.provider_type,
        "base_url": p.base_url,
        "default_model": p.default_model,
        "is_active": bool(p.is_active),
        "enabled": bool(p.is_active),
        "is_default": bool(p.is_default),
        "has_api_key": _has_api_key(p.api_key),
        "api_key": masked,
        "api_key_masked": masked,
        "models": models or [],
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _serialize_model(m: AIModelConfig, provider_name: str | None = None) -> dict:
    """_serialize_model。

    参数说明：
    :param m: 参数 m
    :param provider_name: 参数 provider_name
    :return: 返回处理结果。
    """
    return {
        "id": str(m.id),
        "provider_id": str(m.provider_id),
        "provider_name": provider_name,
        "model_name": m.model_name,
        "model_type": m.model_type,
        "temperature": m.temperature,
        "max_tokens": m.max_tokens,
        "is_active": bool(m.is_active),
        "active": bool(m.is_active),
        "is_default": bool(m.is_default),
        "sort_order": int(m.sort_order or 0),
    }


def _next_model_sort_order(db: Session, provider_id: str) -> int:
    """_next_model_sort_order。

    参数说明：
    :param db: 参数 db
    :param provider_id: 参数 provider_id
    :return: 返回处理结果。
    """
    current = (
        db.query(func.max(AIModelConfig.sort_order))
        .filter(AIModelConfig.provider_id == provider_id)
        .scalar()
    )
    return int(current or 0) + 1


def _order_models_query(query):
    """_order_models_query。

    参数说明：
    :param query: 参数 query
    :return: 返回处理结果。
    """
    return query.order_by(
        AIModelConfig.provider_id.asc(),
        AIModelConfig.sort_order.asc(),
        AIModelConfig.is_default.desc(),
    )


def _apply_provider_patch(p: AIModelProvider, body: AIProviderPatch) -> None:
    """_apply_provider_patch。

    参数说明：
    :param p: 参数 p
    :param body: 参数 body
    :return: 返回处理结果。
    """
    data = body.model_dump(exclude_unset=True)
    if "enabled" in data:
        data["is_active"] = data.pop("enabled")
    if "api_key" in data and not (data["api_key"] or "").strip():
        data.pop("api_key")
    for key, value in data.items():
        if key == "base_url":
            setattr(p, key, value or "")
        elif key == "default_model":
            setattr(p, key, value or "")
        else:
            setattr(p, key, value)


def _ensure_provider_default_model(db: Session, provider: AIModelProvider) -> None:
    """_ensure_provider_default_model。

    参数说明：
    :param db: 参数 db
    :param provider: 参数 provider
    :return: 返回处理结果。
    """
    model_name = (provider.default_model or "").strip()
    if not model_name:
        return
    exists = (
        db.query(AIModelConfig)
        .filter(
            AIModelConfig.provider_id == provider.id,
            AIModelConfig.model_name == model_name,
        )
        .first()
    )
    if exists:
        return
    import uuid
    db.add(
        AIModelConfig(
            id=str(uuid.uuid4()),
            provider_id=provider.id,
            model_name=model_name,
            model_type="chat",
            temperature="0.7",
            max_tokens="4096",
            is_active=True,
            is_default=True,
        )
    )


@router.get("/providers")
def list_providers(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """AI 提供商列表"""
    providers = db.query(AIModelProvider).order_by(AIModelProvider.is_default.desc()).all()
    model_rows = db.query(AIModelConfig).all()
    models_by_provider: dict[str, list[dict]] = {}
    for m in model_rows:
        models_by_provider.setdefault(str(m.provider_id), []).append(
            {"model_name": m.model_name, "model_type": m.model_type, "is_active": bool(m.is_active)}
        )
    data = [_serialize_provider(p, models_by_provider.get(str(p.id), [])) for p in providers]
    return success_response(data=data)


@router.post("/providers")
def create_provider(
    body: AIProviderCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """创建 AI 提供商（同名则更新，避免重复保存失败）"""
    import uuid
    is_active = body.is_active if body.enabled is None else body.enabled
    existing = db.query(AIModelProvider).filter(AIModelProvider.name == body.name).first()
    if existing:
        patch = AIProviderPatch(
            name=body.name,
            provider_type=body.provider_type,
            api_key=body.api_key,
            base_url=body.base_url,
            default_model=body.default_model,
            is_active=is_active,
            is_default=body.is_default,
        )
        _apply_provider_patch(existing, patch)
        if is_active and not _has_api_key(existing.api_key):
            raise HTTPException(status_code=400, detail="请先配置有效的 API Key 再启用提供商")
        _ensure_provider_default_model(db, existing)
        db.commit()
        invalidate_ai_model_cache()
        return success_response(data={"id": str(existing.id)}, message="提供商已更新")

    provider = AIModelProvider(
        id=str(uuid.uuid4()),
        name=body.name,
        provider_type=body.provider_type,
        api_key=body.api_key,
        base_url=body.base_url or "",
        default_model=body.default_model or "",
        is_active=is_active,
        is_default=body.is_default,
    )
    db.add(provider)
    db.flush()
    _ensure_provider_default_model(db, provider)
    db.commit()
    invalidate_ai_model_cache()
    return success_response(data={"id": str(provider.id)}, message="提供商创建成功")


@router.put("/providers/{provider_id}")
def update_provider(
    provider_id: str,
    body: AIProviderPatch,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """更新 AI 提供商（支持仅传 enabled / is_active 切换开关）"""
    p = db.query(AIModelProvider).filter(AIModelProvider.id == provider_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="提供商不存在")
    _apply_provider_patch(p, body)
    if p.is_active and not _has_api_key(p.api_key):
        raise HTTPException(status_code=400, detail="请先配置有效的 API Key 再启用提供商")
    _ensure_provider_default_model(db, p)
    db.commit()
    invalidate_ai_model_cache()
    return success_response(message="提供商更新成功")


@router.delete("/providers/{provider_id}")
def delete_provider(
    provider_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """删除 AI 提供商"""
    p = db.query(AIModelProvider).filter(AIModelProvider.id == provider_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="提供商不存在")
    db.delete(p)
    db.commit()
    invalidate_ai_model_cache()
    return success_response(message="提供商已删除")


@router.get("/models")
def list_models(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    provider_id: Optional[str] = Query(None),
    enriched: bool = Query(False, description="返回能力标签与健康快照"),
):
    """AI 模型列表"""
    if enriched:
        data = build_models_enriched_list(db, provider_id=provider_id)
        return success_response(data=data)

    query = db.query(AIModelConfig)
    if provider_id:
        query = query.filter(AIModelConfig.provider_id == provider_id)

    models = _order_models_query(query).all()
    provider_map = {
        str(p.id): p.name for p in db.query(AIModelProvider).all()
    }
    data = [_serialize_model(m, provider_map.get(str(m.provider_id))) for m in models]
    return success_response(data=data)


@router.post("/models/probe")
def probe_models_status(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    provider_id: Optional[str] = Query(None),
):
    """实时探测已配置模型的可用性（使用提供商 DB 中的 Key）。"""
    report = probe_all_configured_models(db, provider_id=provider_id)
    return success_response(data=report, message="模型可用性探测完成")


@router.post("/models")
def create_model(
    body: AIModelCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """创建 AI 模型配置"""
    import uuid
    is_active = body.is_active if body.active is None else body.active
    sort_order = body.sort_order
    if sort_order is None or sort_order <= 0:
        sort_order = _next_model_sort_order(db, body.provider_id)
    model = AIModelConfig(
        id=str(uuid.uuid4()),
        provider_id=body.provider_id,
        model_name=body.model_name,
        model_type=body.model_type,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        is_active=is_active,
        is_default=body.is_default,
        sort_order=sort_order,
    )
    db.add(model)
    db.commit()
    invalidate_ai_model_cache()
    return success_response(data={"id": str(model.id)}, message="模型创建成功")


@router.put("/models/{model_id}")
def update_model(
    model_id: str,
    body: AIModelPatch,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """更新 AI 模型配置（支持仅传 active / is_active 切换）"""
    model = db.query(AIModelConfig).filter(AIModelConfig.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    data = body.model_dump(exclude_unset=True)
    if "active" in data:
        data["is_active"] = data.pop("active")
    for key, value in data.items():
        setattr(model, key, value)
    db.commit()
    invalidate_ai_model_cache()
    return success_response(message="模型更新成功")


def _mask_key(key: str) -> str:
    """_mask_key。

    参数说明：
    :param key: 参数 key
    :return: 返回处理结果。
    """
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


@router.post("/set-default")
def set_default_model(
    body: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """设置默认 AI 模型"""
    model_id = body.get("model") if isinstance(body, dict) else None
    if not model_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="model is required")
    
    # 清除所有模型的默认标志
    db.query(AIModelConfig).update({"is_default": False})
    # 设置指定模型为默认
    model = db.query(AIModelConfig).filter(AIModelConfig.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    model.is_default = True
    db.commit()
    invalidate_ai_model_cache()
    return success_response(message="默认模型设置成功")


@router.get("/nvidia/catalog")
def get_nvidia_catalog(admin: User = Depends(get_current_super_admin)):
    """NVIDIA NIM 全量模型目录（按推理/文章/视频等场景分类）"""
    return success_response(data=build_nvidia_catalog())


@router.get("/nvidia/scenarios")
def get_nvidia_scenarios(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """按业务场景查看/切换当前绑定的 NVIDIA 模型"""
    return success_response(data=build_scenario_switch_payload(db))


@router.put("/nvidia/scenarios")
def update_nvidia_scenarios(
    body: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """批量保存场景 → 模型映射"""
    mappings = body.get("mappings") if isinstance(body, dict) else None
    if not isinstance(mappings, dict):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="mappings 必须为对象")
    try:
        saved = save_scenario_mappings(db, mappings)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    invalidate_ai_model_cache()
    return success_response(data={"mappings": saved}, message="场景模型已更新")


@router.get("/nvidia/scenarios/health")
def get_nvidia_scenario_health(
    scenario: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """探测各场景绑定模型的连通性（chat / Cosmos）。"""
    if scenario:
        return success_response(data=probe_scenario_health(db, scenario.strip()))
    return success_response(data=probe_all_scenario_health(db))


@router.get("/nvidia/scenarios/health/latest")
def get_nvidia_scenario_health_latest(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """返回最近一次巡检快照（定时任务或 ops 手动触发）。"""
    snapshot = load_health_snapshot(db)
    if not snapshot:
        return success_response(
            data=None,
            message="尚无巡检快照，请执行健康检查或等待定时任务",
        )
    return success_response(data=snapshot)


@router.post("/nvidia/scenarios/health/run")
def run_nvidia_scenario_health_now(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """立即执行全场景健康检查并写入快照。"""
    report = run_scenario_health_check()
    return success_response(data=report, message="健康检查已完成")


@router.post("/test")
def test_ai_connection(
    body: dict | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """探测 AI 提供商连通性"""
    import time
    import httpx
    from app.core.config import settings
    payload = body or {}
    api_key = (payload.get("api_key") or "").strip()
    base_url = (payload.get("base_url") or "").strip()
    platform = (payload.get("platform") or payload.get("provider") or "default").strip()
    if not api_key:
        api_key = (settings.AI_NVIDIA_API_KEY or "").strip()
    if not base_url:
        base_url = (settings.AI_NVIDIA_BASE_URL or "https://integrate.api.nvidia.com/v1").strip()

    model = (payload.get("model") or settings.AI_NVIDIA_MODELS.get("general", "meta/llama-3.1-70b-instruct")).strip()
    if model.startswith("nvidia/cosmos-") and "/v1/infer" not in base_url:
        return success_response(
            data={
                "healthy": True,
                "latency_ms": 0,
                "provider": platform,
                "model": model,
                "skipped_chat_probe": True,
            },
            message="视频类模型需走 /v1/infer，API Key 已通过；请在视频工作流中调用",
        )

    chat_url = f"{base_url.rstrip('/')}/chat/completions"
    started = time.perf_counter()
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                chat_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 16,
                    "temperature": 0.1,
                },
            )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if resp.status_code >= 400:
            detail = resp.text[:300]
            return success_response(
                data={"healthy": False, "latency_ms": latency_ms, "provider": platform, "status_code": resp.status_code},
                message=f"连接失败: HTTP {resp.status_code} {detail}",
            )
        return success_response(
            data={"healthy": True, "latency_ms": latency_ms, "provider": platform, "model": model},
            message="连接正常",
        )
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return success_response(
            data={"healthy": False, "latency_ms": latency_ms, "provider": platform},
            message=f"连接失败: {exc}",
        )
