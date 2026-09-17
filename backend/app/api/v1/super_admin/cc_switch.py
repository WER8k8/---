# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""CC Haha / CC Switch 中转配置管理接口"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.cache import invalidate_cc_switch_cache
from app.core.database import get_db
from app.core.response import success_response
from app.models.ai_config import CCSwitchConfig
from app.models.user import User

router = APIRouter()


class CCSwitchCreate(BaseModel):
    name: str
    provider_type: str = "cc_switch"
    base_url: str
    api_key: Optional[str] = None
    model_mapping: Dict[str, str] = {}
    rate_limit: str = "60"
    is_active: bool = True
    health_check_url: Optional[str] = None


class CCSwitchUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_mapping: Optional[Dict[str, str]] = None
    rate_limit: Optional[str] = None
    is_active: Optional[bool] = None
    health_check_url: Optional[str] = None


@router.get("")
def list_cc_switches(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """CC Switch 配置列表"""
    configs = db.query(CCSwitchConfig).order_by(CCSwitchConfig.created_at.desc()).all()
    data = [{
        "id": str(c.id),
        "name": c.name,
        "provider_type": c.provider_type,
        "base_url": c.base_url,
        "api_key_masked": _mask_key(c.api_key_encrypted),
        "model_mapping": c.model_mapping or {},
        "rate_limit": c.rate_limit,
        "is_active": c.is_active,
        "health_check_url": c.health_check_url,
        "last_health_status": c.last_health_status,
        "last_health_check_at": c.last_health_check_at.isoformat() if c.last_health_check_at else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    } for c in configs]
    return success_response(data=data)


@router.post("")
def create_cc_switch(
    body: CCSwitchCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """创建 CC Switch 配置"""
    import uuid
    config = CCSwitchConfig(
        id=str(uuid.uuid4()),
        name=body.name,
        provider_type=body.provider_type,
        base_url=body.base_url,
        api_key_encrypted=body.api_key or "",
        model_mapping=body.model_mapping,
        rate_limit=body.rate_limit,
        is_active=body.is_active,
        health_check_url=body.health_check_url or "",
    )
    db.add(config)
    db.commit()
    invalidate_cc_switch_cache()
    return success_response(data={"id": str(config.id)}, message="CC Switch 配置创建成功")


@router.put("/{config_id}")
def update_cc_switch(
    config_id: str,
    body: CCSwitchUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """更新 CC Switch 配置"""
    config = db.query(CCSwitchConfig).filter(CCSwitchConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    if body.name is not None:
        config.name = body.name
    if body.base_url is not None:
        config.base_url = body.base_url
    if body.api_key is not None:
        config.api_key_encrypted = body.api_key
    if body.model_mapping is not None:
        config.model_mapping = body.model_mapping
    if body.rate_limit is not None:
        config.rate_limit = body.rate_limit
    if body.is_active is not None:
        config.is_active = body.is_active
    if body.health_check_url is not None:
        config.health_check_url = body.health_check_url

    db.commit()
    invalidate_cc_switch_cache(config_id)
    return success_response(message="CC Switch 配置更新成功")


@router.delete("/{config_id}")
def delete_cc_switch(
    config_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """删除 CC Switch 配置"""
    config = db.query(CCSwitchConfig).filter(CCSwitchConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    db.delete(config)
    db.commit()
    invalidate_cc_switch_cache(config_id)
    return success_response(message="CC Switch 配置已删除")


@router.post("/{config_id}/health-check")
def health_check_cc_switch(
    config_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """手动触发 CC Switch 健康检查"""
    config = db.query(CCSwitchConfig).filter(CCSwitchConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    import httpx
    from datetime import datetime, timezone
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(config.health_check_url or f"{config.base_url}/health")
            config.last_health_status = "ok" if resp.status_code == 200 else "error"
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("健康检查失败: %s", e)
        config.last_health_status = "unreachable"

    config.last_health_check_at = datetime.now(timezone.utc)
    db.commit()
    return success_response(data={"status": config.last_health_status})


def _mask_key(key: Optional[str]) -> Optional[str]:
    """_mask_key。

    参数说明：
    :param key: 参数 key
    :return: 返回处理结果。
    """
    if not key:
        return None
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]
