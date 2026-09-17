# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
System Config API Router - 系统配置API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import get_current_user
from app.models.system_config import SystemConfig
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/system-config"
ROUTE_TAGS = ["系统配置"]

router = APIRouter(tags=["system-config"])


@router.post("/", response_model=dict)
def create_system_config(
    key: str,
    value: str,
    value_type: str = "string",  # string/number/boolean/json
    description: Optional[str] = None,
    is_public: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建系统配置"""
    try:
        config = SystemConfig(
            key=key,
            value=value,
            value_type=value_type,
            description=description,
            is_public=is_public,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return success_response(data={"id": str(config.id), "key": config.key, "value": config.value})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{config_id}", response_model=dict)
def get_system_config(config_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取系统配置详情"""
    config = db.query(SystemConfig).filter(SystemConfig.id == uuid.UUID(config_id)).first()
    if not config:
        raise HTTPException(status_code=404, detail="System config not found")
    
    return success_response(data={
        "id": str(config.id),
        "key": config.key,
        "value": config.value,
        "value_type": config.value_type,
        "description": config.description,
        "is_public": config.is_public,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    })


@router.get("/by-key/{key}", response_model=dict)
def get_system_config_by_key(key: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """根据key获取系统配置"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="System config not found")
    
    return success_response(data={
        "id": str(config.id),
        "key": config.key,
        "value": config.value,
        "value_type": config.value_type,
        "description": config.description,
        "is_public": config.is_public,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    })


@router.put("/{config_id}", response_model=dict)
def update_system_config(
    config_id: str,
    value: Optional[str] = None,
    value_type: Optional[str] = None,
    description: Optional[str] = None,
    is_public: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新系统配置"""
    config = db.query(SystemConfig).filter(SystemConfig.id == uuid.UUID(config_id)).first()
    if not config:
        raise HTTPException(status_code=404, detail="System config not found")
    
    if value is not None:
        config.value = value
    if value_type is not None:
        config.value_type = value_type
    if description is not None:
        config.description = description
    if is_public is not None:
        config.is_public = is_public
    
    db.commit()
    db.refresh(config)
    return success_response(data={"id": str(config.id), "key": config.key, "value": config.value})


@router.delete("/{config_id}")
def delete_system_config(config_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除系统配置"""
    config = db.query(SystemConfig).filter(SystemConfig.id == uuid.UUID(config_id)).first()
    if not config:
        raise HTTPException(status_code=404, detail="System config not found")
    
    db.delete(config)
    db.commit()
    return success_response(message="System config deleted successfully")


@router.get("/", response_model=List[dict])
def list_system_configs(
    is_public: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出系统配置（支持过滤）"""
    query = db.query(SystemConfig)
    if is_public is not None:
        query = query.filter(SystemConfig.is_public == is_public)
    
    configs = query.order_by(SystemConfig.key).offset(skip).limit(limit).all()
    return success_response(data=[
        {
            "id": str(c.id),
            "key": c.key,
            "value": c.value,
            "value_type": c.value_type,
            "is_public": c.is_public,
            "description": c.description,
        }
        for c in configs
    ])
