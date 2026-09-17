# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""客户流失预警 API"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.churn_service import ChurnService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["客户流失预警"]

router = APIRouter(prefix="/churn", tags=["客户流失预警"])


def _serialize_tenant(raw: dict, contacted_ids: set[str]) -> dict:
    """将服务层字段映射为前端 churn-warning.vue 契约。"""
    reasons = raw.get("reasons") or []
    phone = (raw.get("contact_phone") or "").strip()
    email = (raw.get("contact_email") or "").strip()
    name = (raw.get("contact_name") or "").strip()
    contact = " / ".join(x for x in (phone, email, name) if x) or "-"
    updated = raw.get("updated_at") or ""
    tid = str(raw.get("id", ""))
    risk = raw.get("risk_level") or raw.get("risk") or "low"
    return {
        "id": tid,
        "name": raw.get("name") or "-",
        "risk": risk,
        "risk_level": risk,
        "risk_score": raw.get("risk_score"),
        "reason": "；".join(reasons) if reasons else "暂无明显风险",
        "reasons": reasons,
        "last_login": updated[:10] if updated else "-",
        "contact": contact,
        "contacted": tid in contacted_ids,
        "expires_at": raw.get("expires_at"),
        "status": raw.get("status"),
    }


@router.get("/at-risk")
def get_at_risk_tenants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取有流失风险的租户列表"""
    tenants_raw = ChurnService.get_at_risk_tenants(db)
    contacted = set(ChurnService.get_contacted_list(db))
    tenants = [_serialize_tenant(t, contacted) for t in tenants_raw]
    data = {
        "tenants": tenants,
        "summary": {
            "total": len(tenants),
            "high": sum(1 for t in tenants if t["risk"] == "high"),
            "medium": sum(1 for t in tenants if t["risk"] == "medium"),
            "low": sum(1 for t in tenants if t["risk"] == "low"),
        },
    }
    return success_response(data=data)


@router.get("/tips")
def get_retention_tips(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取挽留建议"""
    tips = ChurnService.get_retention_tips(db)
    return success_response(data=tips)


@router.post("/mark-contacted/{tenant_id}")
def mark_contacted(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记客户为已联系"""
    result = ChurnService.mark_contacted(db, tenant_id)
    return success_response(data=result)


@router.get("/trend")
def get_churn_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取流失趋势"""
    trend = ChurnService.get_churn_trend(db)
    return success_response(data=trend)
