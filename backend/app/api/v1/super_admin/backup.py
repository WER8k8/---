# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""自动备份 API"""

import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.admin_auth import get_current_super_admin
from app.core.response import success_response
from app.models.user import User
from app.services.auto_backup import backup_service
from app.services.backup_service import BackupService

router = APIRouter()


class RestoreRequest(BaseModel):
    filename: str = Field(..., min_length=1, description="backups/ 下的备份文件名")


def _safe_backup_name(filename: str) -> str:
    name = os.path.basename(filename.strip())
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="非法备份文件名")
    if not name.startswith("backup_") or not name.endswith(".db"):
        raise HTTPException(status_code=400, detail="仅支持 backup_*.db 备份文件")
    return name


@router.get("/status")
def backup_status(user: User = Depends(get_current_super_admin)):
    """backup_status。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    return success_response(data=backup_service.get_status())


@router.get("/list")
def list_backups(user: User = Depends(get_current_super_admin)):
    """历史备份列表（auto_backup 目录 + BackupService 文件备份）"""
    status = backup_service.get_status()
    file_backups = BackupService.list_backups()
    return success_response(data={
        "items": file_backups,
        "auto_backups": status.get("recent_backups", []),
        "backup_dir": status.get("backup_dir"),
        "total": len(file_backups),
    })


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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore")
def restore_backup(
    body: RestoreRequest,
    user: User = Depends(get_current_super_admin),
):
    """从历史备份恢复（backup_*.db）"""
    name = _safe_backup_name(body.filename)
    result = BackupService.restore_backup(name)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "备份文件不存在"))
    return success_response(data=result, message="备份已恢复")
