"""AI模型配置API路由"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import require_admin
from app.schemas.ai_config import (AIModelConfigCreate, AIModelConfigResponse,
                                   AIModelConfigUpdate, AIModelProviderCreate,
                                   AIModelProviderResponse,
                                   AIModelProviderUpdate, AIUsageStatsResponse,
                                   CurrentModelResponse, ModelListResponse,
                                   ModelSwitchRequest, ProviderListResponse)
from app.services.ai_config_service import AIConfigService

router = APIRouter(prefix="/ai-config", tags=["AI配置"])


# ============ Provider Routes ============


@router.get("/providers", response_model=ProviderListResponse)
def list_providers(
        is_active: Optional[bool] = None,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """获取AI模型提供商列表"""
    service = AIConfigService(db)
    providers = service.list_providers(is_active=is_active)
    return ProviderListResponse(
        items=[
            AIModelProviderResponse.model_validate(p) for p in providers],
        total=len(providers))


@router.get("/providers/{provider_id}", response_model=AIModelProviderResponse)
def get_provider(
        provider_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """获取单个提供商详情"""
    service = AIConfigService(db)
    provider = service.get_provider_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="提供商不存在")
    return AIModelProviderResponse.model_validate(provider)


@router.post("/providers",
             response_model=AIModelProviderResponse,
             status_code=201)
def create_provider(
        req: AIModelProviderCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """创建新的AI模型提供商"""
    service = AIConfigService(db)
    try:
        provider = service.create_provider(req)
        return AIModelProviderResponse.model_validate(provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/providers/{provider_id}", response_model=AIModelProviderResponse)
def update_provider(
        provider_id: str,
        req: AIModelProviderUpdate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """更新提供商配置"""
    service = AIConfigService(db)
    try:
        provider = service.update_provider(provider_id, req)
        if not provider:
            raise HTTPException(status_code=404, detail="提供商不存在")
        return AIModelProviderResponse.model_validate(provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/providers/{provider_id}", status_code=204)
def delete_provider(
        provider_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """删除提供商"""
    service = AIConfigService(db)
    if not service.delete_provider(provider_id):
        raise HTTPException(status_code=404, detail="提供商不存在")


@router.post("/providers/{provider_id}/set-default",
             response_model=AIModelProviderResponse)
def set_default_provider(
        provider_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """设置默认提供商"""
    service = AIConfigService(db)
    try:
        provider = service.set_default_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="提供商不存在")
        return AIModelProviderResponse.model_validate(provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Model Config Routes ============


@router.get("/models", response_model=ModelListResponse)
def list_models(
    provider_id: Optional[str] = None,
    model_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """获取模型配置列表"""
    service = AIConfigService(db)
    models = service.list_model_configs(
        provider_id=provider_id,
        model_type=model_type,
        is_active=is_active)

    # 获取提供商名称映射
    provider_names = {}
    for model in models:
        if model.provider_id not in provider_names:
            provider = service.get_provider_by_id(model.provider_id)
            provider_names[model.provider_id] = provider.name if provider else None

    response_items = []
    for model in models:
        response = AIModelConfigResponse.model_validate(model)
        response.provider_name = provider_names.get(model.provider_id)
        response_items.append(response)

    return ModelListResponse(items=response_items, total=len(models))


@router.get("/models/{config_id}", response_model=AIModelConfigResponse)
def get_model_config(
        config_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """获取单个模型配置详情"""
    service = AIConfigService(db)
    model = service.get_model_config_by_id(config_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    provider = service.get_provider_by_id(model.provider_id)
    response = AIModelConfigResponse.model_validate(model)
    response.provider_name = provider.name if provider else None
    return response


@router.post("/models", response_model=AIModelConfigResponse, status_code=201)
def create_model_config(
        req: AIModelConfigCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """创建新的模型配置"""
    service = AIConfigService(db)
    try:
        model = service.create_model_config(req)
        provider = service.get_provider_by_id(model.provider_id)
        response = AIModelConfigResponse.model_validate(model)
        response.provider_name = provider.name if provider else None
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/models/{config_id}", response_model=AIModelConfigResponse)
def update_model_config(
        config_id: str,
        req: AIModelConfigUpdate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """更新模型配置"""
    service = AIConfigService(db)
    model = service.update_model_config(config_id, req)
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    provider = service.get_provider_by_id(model.provider_id)
    response = AIModelConfigResponse.model_validate(model)
    response.provider_name = provider.name if provider else None
    return response


@router.delete("/models/{config_id}", status_code=204)
def delete_model_config(
        config_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """删除模型配置"""
    service = AIConfigService(db)
    if not service.delete_model_config(config_id):
        raise HTTPException(status_code=404, detail="模型配置不存在")


# ============ Model Switch Routes ============


@router.get("/current-model", response_model=CurrentModelResponse)
def get_current_model(
        model_type: str = Query("general"),
        db: Session = Depends(get_db)):
    """获取当前使用的模型配置"""
    service = AIConfigService(db)
    current_model = service.get_current_model(model_type=model_type)
    if not current_model:
        raise HTTPException(status_code=404, detail="未配置任何模型")
    return current_model


@router.post("/switch-model")
def switch_model(
        req: ModelSwitchRequest,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """切换当前使用的AI模型提供商"""
    service = AIConfigService(db)
    # 验证提供商是否存在且活跃
    provider = service.get_provider_by_id(req.provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="提供商不存在")
    if not provider.is_active:
        raise HTTPException(status_code=400, detail="提供商未激活")

    # 设置为默认提供商
    try:
        service.set_default_provider(req.provider_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 获取当前模型信息
    current_model = service.get_current_model(model_type=req.model_type)
    if not current_model:
        raise HTTPException(status_code=500, detail="切换失败，未找到可用模型")

    return success_response(data={"message": "模型切换成功", "current_model": current_model})


# ============ Usage Stats Routes ============


@router.get("/usage/stats", response_model=AIUsageStatsResponse)
def get_usage_stats(
    provider_id: Optional[str] = None,
    days: int = Query(30),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """获取AI使用统计"""
    service = AIConfigService(db)
    return service.get_usage_stats(provider_id=provider_id, days=days)


@router.get("/usage/logs")
def get_usage_logs(
    provider_id: Optional[str] = None,
    task_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """获取AI使用日志列表"""
    service = AIConfigService(db)
    logs = service.get_usage_logs(
        provider_id=provider_id,
        task_type=task_type,
        page=page,
        page_size=page_size)

    provider_names = {}
    for log in logs:
        if log.provider_id not in provider_names:
            provider = service.get_provider_by_id(log.provider_id)
            provider_names[log.provider_id] = provider.name if provider else None

    return success_response(data={
        "data": [
            {
                "id": log.id,
                "provider_id": log.provider_id,
                "provider_name": provider_names.get(log.provider_id),
                "model_name": log.model_name,
                "task_type": log.task_type,
                "prompt_tokens": int(log.prompt_tokens) if log.prompt_tokens else 0,
                "completion_tokens": int(log.completion_tokens) if log.completion_tokens else 0,
                "total_tokens": int(log.total_tokens) if log.total_tokens else 0,
                "cost": float(log.cost) if log.cost else 0.0,
                "duration_ms": int(log.duration_ms) if log.duration_ms else 0,
                "success": log.success,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": len(logs),
        "page": page,
        "page_size": page_size,
    })
