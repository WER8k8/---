import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, require_admin
from app.models.user import User, OperationLog
from app.models.inquiry import Inquiry
from app.schemas.user import LoginRequest, TokenResponse
from app.schemas.inquiry import InquiryCreate, InquiryResponse
from app.core.config import settings

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()


@router.get("/health")
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected",
        "debug_mode": settings.DEBUG,
    }


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录接口"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token)


@router.post("/contact", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def submit_contact(req: InquiryCreate, db: Session = Depends(get_db)):
    """提交联系表单"""
    inquiry = Inquiry(
        name=req.name,
        phone=req.phone,
        email=req.email,
        product=req.product,
        message=req.message,
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return inquiry


@router.get("/audit/logs")
def get_audit_logs(
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
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
        query = query.filter(OperationLog.created_at >= start_time.replace(tzinfo=timezone.utc))
    if end_time:
        query = query.filter(OperationLog.created_at <= end_time.replace(tzinfo=timezone.utc))
    
    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "data": [
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
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/audit/logs/{log_id}")
def get_audit_log_detail(log_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    """获取审计日志详情"""
    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    
    user_info = None
    if log.user_id:
        user = db.query(User).filter(User.id == log.user_id).first()
        if user:
            user_info = {"id": str(user.id), "username": user.username, "display_name": user.display_name}
    
    return {
        "id": str(log.id),
        "user_id": log.user_id,
        "user_info": user_info,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "detail": log.detail,
        "ip_address": log.ip_address,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


@router.delete("/audit/logs/{log_id}")
def delete_audit_log(log_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    """删除单条审计日志"""
    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    
    db.delete(log)
    db.commit()
    return {"message": "日志删除成功"}


@router.delete("/audit/logs")
def clear_audit_logs(
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
    before_date: datetime = Query(None),
):
    """批量删除审计日志"""
    query = db.query(OperationLog)
    if before_date:
        query = query.filter(OperationLog.created_at <= before_date.replace(tzinfo=timezone.utc))
    
    deleted_count = query.delete()
    db.commit()
    return {"message": f"已删除 {deleted_count} 条日志"}
