# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.field_crypto import decrypt_field
from app.core.response import success_response
from app.core.security import (create_access_token, require_admin,
                               verify_password)
from app.models.inquiry import Inquiry
from app.models.user import OperationLog, User
from app.schemas.inquiry import InquiryCreate, InquiryResponse
from app.schemas.user import LoginRequest, TokenResponse

UPLOAD_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(__file__)))),
    "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()


def _try_decrypt(value: str) -> str:
    """尝试解密，兼容历史明文数据。"""
    if not value:
        return value
    try:
        return decrypt_field(value)
    except Exception:
        return value

# 注意：GET /system/health 由 app.api.v1.routes.system 优先注册；此处不再重复定义 health，避免双路由。


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录接口（遗留路径，与 /auth/login 并存）"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误")
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return success_response(data=TokenResponse(access_token=token))


@router.post("/contact", status_code=status.HTTP_201_CREATED)
def submit_contact(req: InquiryCreate, db: Session = Depends(get_db)):
    """提交联系表单"""
    inquiry = Inquiry(
        name=req.name,
        phone=req.phone,
        email=req.email,
        product=req.product_interest or "",
        message=req.message,
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    body = success_response(data=InquiryResponse.model_validate(inquiry))
    return JSONResponse(status_code=201, content=body.model_dump(mode="json"))


@router.get("/audit/logs")
def get_audit_logs(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Query(None),
    action: str = Query(None),
    resource_type: str = Query(None),
    start_time: datetime = Query(None),
    end_time: datetime = Query(None),
):
    """获取审计日志列表"""
    query = db.query(OperationLog).order_by(desc(OperationLog.created_at))
    if user_id:
        query = query.filter(OperationLog.user_id == user_id)
    if action:
        query = query.filter(OperationLog.action == action)
    if resource_type:
        query = query.filter(OperationLog.resource_type == resource_type)
    if start_time:
        query = query.filter(
            OperationLog.created_at >= start_time.replace(
                tzinfo=timezone.utc))
    if end_time:
        query = query.filter(
            OperationLog.created_at <= end_time.replace(
                tzinfo=timezone.utc))

    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    rows = [
        {
            "id": str(log.id),
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "detail": log.detail,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
    return success_response(
        data=rows,
        total=total,
        page=page,
        page_size=page_size)


@router.get("/audit/logs/{log_id}")
def get_audit_log_detail(
        log_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """获取审计日志详情"""
    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")

    user_info = None
    if log.user_id:
        user = db.query(User).filter(User.id == log.user_id).first()
        if user:
            user_info = {
                "id": str(
                    user.id),
                "username": user.username,
                "display_name": user.display_name}

    return success_response(
        data={
            "id": str(
                log.id),
            "user_id": log.user_id,
            "user_info": user_info,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "detail": log.detail,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })


@router.delete("/audit/logs/{log_id}")
def delete_audit_log(
        log_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """删除单条审计日志"""
    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")

    db.delete(log)
    db.commit()
    return success_response(message="日志删除成功")


@router.delete("/audit/logs")
def clear_audit_logs(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
    before_date: datetime = Query(None),
):
    """批量删除审计日志"""
    query = db.query(OperationLog)
    if before_date:
        query = query.filter(
            OperationLog.created_at <= before_date.replace(
                tzinfo=timezone.utc))

    deleted_count = query.delete()
    db.commit()
    return success_response(message=f"已删除 {deleted_count} 条日志")


@router.get("/users")
def list_users(db: Session = Depends(get_db), admin=Depends(require_admin)):
    """获取用户列表（管理员权限）"""
    users = db.query(User).all()
    rows = [
        {
            "id": str(user.id),
            "username": user.username,
            "email": _try_decrypt(user.email),
            "display_name": user.display_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        for user in users
    ]
    return success_response(data=rows, total=len(rows))
