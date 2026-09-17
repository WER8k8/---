# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI 内容生成模板 API"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.ai_template import AITemplate


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["AI模板管理"]

router = APIRouter(prefix="/ai/templates", tags=["AI模板管理"])


class AITemplateCreate(BaseModel):
    name: str = Field(..., max_length=100)
    task_type: str = Field(..., max_length=30)
    system_prompt: Optional[str] = None
    user_prompt_template: str
    variables_json: str = "[]"
    default_params_json: str = '{"temperature":0.7,"max_tokens":2000}'
    is_active: bool = True
    sort_order: int = 0


class AITemplateUpdate(BaseModel):
    name: Optional[str] = None
    task_type: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    variables_json: Optional[str] = None
    default_params_json: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


@router.get("")
def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    task_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出（list_templates）：处理相关业务逻辑并返回结果。

    :param page: 入参 (int)。
    :param page_size: 入参 (int)。
    :param task_type: 入参 (Optional[str])。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ("admin", "super_admin", "tenant_admin"):
        return error_response(403, "权限不足")
    q = db.query(AITemplate)
    if task_type:
        q = q.filter(AITemplate.task_type == task_type)
    total = q.count()
    items = q.order_by(AITemplate.sort_order.desc(), AITemplate.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return success_response(data={
        "items": [t.to_dict() for t in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("")
def create_template(
    body: AITemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建（create_template）：处理相关业务逻辑并返回结果。

    :param body: 入参 (AITemplateCreate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "仅管理员可创建模板")
    t = AITemplate(
        name=body.name,
        task_type=body.task_type,
        system_prompt=body.system_prompt,
        user_prompt_template=body.user_prompt_template,
        variables_json=body.variables_json,
        default_params_json=body.default_params_json,
        is_active=body.is_active,
        sort_order=body.sort_order,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return success_response(data=t.to_dict(), message="创建成功")


@router.put("/{tpl_id}")
def update_template(
    tpl_id: str,
    body: AITemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新（update_template）：处理相关业务逻辑并返回结果。

    :param tpl_id: 入参 (str)。
    :param body: 入参 (AITemplateUpdate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "仅管理员可编辑模板")
    t = db.query(AITemplate).filter(AITemplate.id == tpl_id).first()
    if not t:
        return error_response(404, "模板不存在")
    for k, v in body.dict(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return success_response(data=t.to_dict(), message="更新成功")


@router.delete("/{tpl_id}")
def delete_template(
    tpl_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除（delete_template）：处理相关业务逻辑并返回结果。

    :param tpl_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "仅管理员可删除模板")
    t = db.query(AITemplate).filter(AITemplate.id == tpl_id).first()
    if not t:
        return error_response(404, "模板不存在")
    db.delete(t)
    db.commit()
    return success_response(message="删除成功")
