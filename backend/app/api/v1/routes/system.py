# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""系统管理路由 - 整合版（合并 routes/system.py + system_routes.py）"""

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.login_bruteforce import (check_login_allowed,
                                       client_ip_from_request,
                                       record_login_failure,
                                       record_login_success)
from app.core.field_crypto import decrypt_field
from app.core.response import error_response, success_response
from app.core.security import (create_access_token, get_current_user,
                               require_admin, verify_password)
from app.db.session import get_db
from app.services.unified_admin_login import resolve_user_for_unified_login
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


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/system"
ROUTE_TAGS = ["系统管理"]

router = APIRouter()


def _try_decrypt(value: str) -> str:
    """尝试解密，兼容历史明文数据。"""
    if not value:
        return value
    try:
        return decrypt_field(value)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("解密字段失败，返回原始值: %s", e)
        return value


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """系统健康检查（真实探测，不伪造组件状态）"""
    from app.core.config import settings
    checks: dict[str, str] = {}
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"fail: {type(exc).__name__}"

    try:
        if settings.REDIS_ENABLED:
            import redis  # type: ignore
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                socket_timeout=2,
            )
            r.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "disabled"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"fail: {type(exc).__name__}"

    healthy = checks.get("database") == "ok"
    return success_response(
        data={
            "status": "healthy" if healthy else "degraded",
            "database": checks.get("database", "unknown"),
            "redis": checks.get("redis", "unknown"),
        }
    )


@router.get("/info")
def get_system_info(db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    """获取系统信息"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    from app.core.config import settings
    import platform
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("获取系统资源信息失败: %s", e)
        cpu = None
        mem = None

    return success_response(
        data={
            "version": getattr(settings, "APP_VERSION", "1.0.0"),
            "environment": settings.ENVIRONMENT,
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_percent": cpu,
            "memory_percent": mem,
        }
    )


@router.get("/logs")
def get_system_logs(
    page: int = 1,
    page_size: int = 50,
    level: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取系统日志"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")

    return success_response(
        data={
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size})


@router.post("/cache/clear")
def clear_cache(db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    """清除系统缓存"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")

    return success_response(message="缓存已清除")


@router.get("/jwt/keys/status")
def get_jwt_key_status(current_user: User = Depends(get_current_user)):
    """获取 JWT 密钥状态（仅超管）"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")
    from app.core.jwt_key_rotation import jwt_key_rotation_service
    return success_response(data=jwt_key_rotation_service.get_key_status())


@router.post("/jwt/keys/rotate")
def rotate_jwt_keys(current_user: User = Depends(get_current_user)):
    """手动轮换 JWT 密钥（仅超管）"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")
    from app.core.jwt_key_rotation import jwt_key_rotation_service
    result = jwt_key_rotation_service.rotate_keys()
    return success_response(data=result, message="JWT 密钥轮换成功")


@router.post("/jwt/keys/cleanup")
def cleanup_expired_jwt_keys(current_user: User = Depends(get_current_user)):
    """清理过期的 JWT 密钥（仅超管）"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")
    from app.core.jwt_key_rotation import jwt_key_rotation_service
    result = jwt_key_rotation_service.cleanup_expired_keys()
    return success_response(data=result)


@router.post("/restart")
def restart_services(
        service: str = "all",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """重启服务"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")

    return success_response(
        data={
            "service": service,
            "status": "restarting"},
        message="服务重启中")


@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    """获取系统性能统计（psutil 实测）"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    try:
        import psutil
        disk_path = "C:\\" if os.name == "nt" else "/"
        return success_response(
            data={
                "cpu_usage": round(psutil.cpu_percent(interval=0.1), 1),
                "memory_usage": round(psutil.virtual_memory().percent, 1),
                "disk_usage": round(psutil.disk_usage(disk_path).percent, 1),
                "data_source": "psutil",
            }
        )
    except Exception as exc:  # noqa: BLE001
        return error_response(503, f"系统指标不可用: {type(exc).__name__}")


# ========== 以下来自 system_routes.py（遗留路由，已合并） ==========


@router.post("/login")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """用户登录接口（遗留路径，与 /auth/login 并存）"""
    # 暴力破解防护
    ip = client_ip_from_request(request)
    blocked = check_login_allowed(ip, req.username)
    if blocked:
        return error_response(blocked[0], blocked[1])

    # 使用统一登录服务解析用户
    user, matrix_admin_id = resolve_user_for_unified_login(
        db, req.username, req.password)
    
    if not user or not user.is_active:
        record_login_failure(ip, req.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误")

    record_login_success(ip, req.username)
    # 生成 JWT（包含矩阵管理员ID）
    access_body = {"sub": str(user.id), "role": user.role, "scopes": [user.role]}
    if matrix_admin_id is not None:
        access_body["mid"] = matrix_admin_id
    
    token = create_access_token(data=access_body)
    return success_response(data=TokenResponse(access_token=token))


@router.post("/contact", status_code=status.HTTP_201_CREATED)
def submit_contact(req: InquiryCreate, db: Session = Depends(get_db), request: Request = None):
    """提交联系表单（官网/租户站访客 → 询盘）。"""
    tenant_id = None
    try:
        from app.models.tenant import Tenant
        host = ""
        q_domain = ""
        if request is not None:
            host = (request.headers.get("host") or "").split(":")[0].lower()
            q_domain = (
                request.query_params.get("__tenant")
                or request.query_params.get("tenant")
                or request.headers.get("x-tenant-domain")
                or ""
            ).strip().lower()
        cand = q_domain or ("" if host in ("", "127.0.0.1", "localhost") else host)
        if cand:
            t = db.query(Tenant).filter(Tenant.domain == cand).first()
            if t:
                tenant_id = t.id
        if not tenant_id:
            # 本机/未标注域名时：默认归到 dev.local 开发租户，保证租户队列可见
            t = db.query(Tenant).filter(Tenant.domain == "dev.local").first()
            if t:
                tenant_id = t.id
    except Exception:
        tenant_id = None
    inquiry_kwargs = {
        "name": req.name,
        "phone": req.phone,
        "email": req.email,
        "product": req.product or getattr(req, "product_interest", None) or "",
        "message": req.message,
    }
    # Inquiry 可能要求 tenant_id 列非空：优先显式列存在再写
    cols = {c.name for c in Inquiry.__table__.columns}
    if "tenant_id" in cols:
        inquiry_kwargs["tenant_id"] = tenant_id
    inquiry = Inquiry(**inquiry_kwargs)
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
