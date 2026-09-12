"""超级管理员 - 租户管理接口"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User

router = APIRouter()


@router.get("/")
def list_tenants(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    search: Optional[str] = Query(None),
):
    """租户列表（超级管理员）"""
    return success_response(data={
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    })
