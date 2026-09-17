# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""自动备份 API"""

from fastapi import APIRouter, Depends
from app.core.admin_auth import get_current_super_admin
from app.core.response import success_response
from app.models.user import User
from app.services.auto_backup import backup_service

router = APIRouter()


@router.get("/status")
def backup_status(user: User = Depends(get_current_super_admin)):
    """backup_status。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    return success_response(data=backup_service.get_status())


@router.post("/run")
def run_backup(user: User = Depends(get_current_super_admin)):
    """run_backup。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    try:
        result = backup_service.run_backup()
        return success_response(data=result, message="备份完成")
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
