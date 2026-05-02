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
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.schemas.inquiry import InquiryCreate, InquiryResponse

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

@router.post("/upload")
async def system_upload(file: UploadFile = File(...), admin = Depends(require_admin)):
    ALLOWED_TYPES = {
        "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp",
        "application/pdf": ".pdf",
        "application/dwg": ".dwg", "image/vnd.dwg": ".dwg",
        "application/dxf": ".dxf",
        "application/msword": ".doc", "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.ms-excel": ".xls", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    }
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    content_type_ext = ALLOWED_TYPES.get(file.content_type, "")
    if content_type_ext and f".{ext}" != content_type_ext:
        ext = content_type_ext.lstrip(".")
    if not ext:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 20MB")
    with open(filepath, "wb") as f:
        f.write(content)
    return {"url": f"/uploads/{filename}", "filename": file.filename, "size": len(content)}

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "轻集料混凝土SEO系统运行正常"}

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token)

@router.post("/users", response_model=UserResponse)
def create_user(req: UserCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    existing = db.query(User).filter((User.username == req.username) | (User.email == req.email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或邮箱已存在")
    user = User(username=req.username, email=req.email, hashed_password=get_password_hash(req.password), display_name=req.display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    query = db.query(User).order_by(desc(User.created_at))
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": users, "total": total}


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, req: dict, db: Session = Depends(get_db), admin = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if "username" in req:
        existing = db.query(User).filter(User.username == req["username"], User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = req["username"]
    
    if "email" in req:
        existing = db.query(User).filter(User.email == req["email"], User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已存在")
        user.email = req["email"]
    
    if "password" in req and req["password"]:
        user.hashed_password = get_password_hash(req["password"])
    
    if "role" in req:
        user.role = req["role"]
    
    if "is_active" in req:
        user.is_active = req["is_active"]
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"message": "删除成功"}

@router.post("/contact", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def submit_contact(req: InquiryCreate, db: Session = Depends(get_db)):
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
    query = db.query(OperationLog)
    if before_date:
        query = query.filter(OperationLog.created_at <= before_date.replace(tzinfo=timezone.utc))
    
    deleted_count = query.delete()
    db.commit()
    return {"message": f"已删除 {deleted_count} 条日志"}


@router.get("/ai-config")
def get_ai_config(admin = Depends(require_admin)):
    return {
        "default_model": "gpt-4o",
        "available_models": ["gpt-4o", "claude-3-opus", "gemini-1.5-pro", "deepseek-chat"],
        "temperature": 0.7,
        "max_tokens": 4096,
        "monthly_budget": 1000,
        "total_spent": 0,
    }


@router.put("/ai-config")
def update_ai_config(
    config: dict,
    admin = Depends(require_admin)
):
    return {
        "message": "AI配置更新成功",
        **config
    }


@router.get("/logs")
def get_logs(
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(OperationLog).order_by(desc(OperationLog.created_at))
    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [
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