# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Project Intelligence 路由 — 项目/招标情报（Phase 4）。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.project import Project, ProjectSignal
from app.models.user import User

router = APIRouter()


def _serialize(p: Project) -> dict[str, Any]:
    """执行 serialize 相关逻辑处理。
    
    :param p: 参数 p
    :return: 返回处理结果。
    """
    return {
        "id": str(p.id),
        "name": p.name,
        "company": p.company,
        "company_id": p.company_id,
        "country": p.country,
        "city": p.city,
        "project_type": p.project_type,
        "stage": p.stage,
        "estimated_value": p.estimated_value,
        "currency": p.currency,
        "requirements": p.requirements,
        "matched_product_ids": p.matched_product_ids,
        "product_match_score": p.product_match_score,
        "source": p.source,
        "source_url": p.source_url,
        "confidence": p.confidence,
        "retrieved_at": p.retrieved_at.isoformat() if p.retrieved_at else None,
        "signals": [
            {
                "signal_type": s.signal_type,
                "title": s.title,
                "source_url": s.source_url,
                "occurred_at": s.occurred_at.isoformat() if s.occurred_at else None,
            }
            for s in (p.signals or [])
            if getattr(s, "deleted_at", None) is None
        ],
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.get("", summary="项目情报列表")
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    country: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    project_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行 list_projects 相关数据处理。
    
    :param page: 页码
    :param page_size: 每页条数
    :param country: 参数 country
    :param stage: 参数 stage
    :param project_type: 参数 project_type
    :param search: 搜索关键字
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    q = db.query(Project).filter(Project.deleted_at.is_(None))
    if country:
        q = q.filter(Project.country == country)
    if stage:
        q = q.filter(Project.stage == stage)
    if project_type:
        q = q.filter(Project.project_type == project_type)
    if search:
        like = f"%{search}%"
        q = q.filter((Project.name.ilike(like)) | (Project.company.ilike(like)))
    total = q.count()
    items = (
        q.order_by(Project.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success_response(
        data={"items": [_serialize(p) for p in items], "total": total, "page": page, "page_size": page_size},
        total=total, page=page, page_size=page_size,
    )


@router.get("/stats", summary="项目情报统计")
def project_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /stats 请求，project相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    from sqlalchemy import func as sa_func
    total = db.query(Project).filter(Project.deleted_at.is_(None)).count()
    by_stage = dict(
        db.query(Project.stage, sa_func.count(Project.id))
        .filter(Project.deleted_at.is_(None))
        .group_by(Project.stage)
        .all()
    )
    by_type = dict(
        db.query(Project.project_type, sa_func.count(Project.id))
        .filter(Project.deleted_at.is_(None))
        .group_by(Project.project_type)
        .all()
    )
    return success_response(data={
        "total": total,
        "by_stage": {k: int(v) for k, v in by_stage.items()},
        "by_type": {k: int(v) for k, v in by_type.items()},
    })


@router.get("/{project_id}", summary="项目详情")
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /{project_id} 请求，获取相关资源。
    
    :param project_id: 项目ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    p = db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
    if not p:
        return error_response(404, "项目不存在")
    return success_response(data=_serialize(p))


from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    company: Optional[str] = Field(None, max_length=300)
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    project_type: Optional[str] = Field(None, max_length=100)
    stage: Optional[str] = Field(None, max_length=50)
    estimated_value: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field("USD", max_length=10)
    requirements: Optional[str] = None
    source: Optional[str] = Field(None, max_length=50)
    source_url: Optional[str] = Field(None, max_length=1000)
    confidence: Optional[float] = Field(None, ge=0, le=1)


@router.post("", summary="创建项目情报")
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行 create_project 相关数据处理。
    
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    p = Project(
        name=body.name,
        company=body.company,
        country=body.country,
        city=body.city,
        project_type=body.project_type,
        stage=body.stage or "Announced",
        estimated_value=body.estimated_value,
        currency=body.currency,
        requirements=body.requirements,
        source=body.source,
        source_url=body.source_url,
        confidence=body.confidence,
        retrieved_at=datetime.now(timezone.utc),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return success_response(data=_serialize(p), message="项目已创建")
