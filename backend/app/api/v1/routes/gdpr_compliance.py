# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GDPR 出海隐私合规路由模块。"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.services.gdpr_compliance_service import GDPRComplianceService

router = APIRouter(prefix="/compliance/gdpr", tags=["GDPR Compliance"])

ROUTE_PREFIX = ""
ROUTE_TAGS = ["GDPR Compliance"]


class AnonymizeRequest(BaseModel):
    user_id: str


@router.get("/export/{user_id}", summary="导出符合 GDPR 标准的用户完整数据")
def export_user_gdpr_data(
    user_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, Any]:
    svc = GDPRComplianceService(db)
    data = svc.export_user_data(user_id)
    if "error" in data:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"code": 0, "msg": "ok", "data": data}


@router.post("/anonymize", summary="GDPR 被遗忘权 - 匿名化用户数据")
def anonymize_user(
    req: AnonymizeRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, Any]:
    svc = GDPRComplianceService(db)
    ok = svc.anonymize_user(req.user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="用户不存在或匿名化失败")
    return {"code": 0, "msg": "用户已成功匿名化并销毁隐私标识"}
