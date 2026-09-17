# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, optional_auth
from app.models.seo import AiOptimizationLog, SiteAudit
from app.models.user import User
from app.schemas.seo import SiteAuditCreate, SiteAuditResponse
from app.services.site_audit import (run_full_audit_service,
                                     run_quick_audit_service)

router = APIRouter(tags=["站点审计"])


@router.post("", response_model=SiteAuditResponse)
def create_audit(
        audit_data: SiteAuditCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(optional_auth)):
    """create_audit。

    参数说明：
    :param audit_data: 参数 audit_data
    :param db: 参数 db
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    if audit_data.audit_type == "full":
        result = run_full_audit_service(db, audit_data)
    elif audit_data.audit_type == "quick":
        result = run_quick_audit_service(db, audit_data)
    else:
        raise HTTPException(status_code=400, detail="无效的审计类型，支持 full / quick")
    return result


@router.get("", response_model=list[SiteAuditResponse])
def list_audits(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """list_audits。

    参数说明：
    :param skip: 参数 skip
    :param limit: 参数 limit
    :param db: 参数 db
    :return: 返回处理结果。
    """
    return db.query(SiteAudit).order_by(
        SiteAudit.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{audit_id}", response_model=SiteAuditResponse)
def get_audit(audit_id: str, db: Session = Depends(get_db)):
    """get_audit。

    参数说明：
    :param audit_id: 参数 audit_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    record = db.query(SiteAudit).filter(SiteAudit.id == audit_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="审计记录不存在")
    return record
