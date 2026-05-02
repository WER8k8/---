from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, require_admin
from app.core.permissions import Role, has_permission, get_role_label
from app.models.user import User

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: Optional[str] = None
    role: str = "editor"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: Optional[str]
    role: str
    role_label: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), admin = Depends(require_admin)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        UserResponse(
            id=str(u.id),
            username=u.username,
            email=u.email,
            display_name=u.display_name,
            role=u.role,
            role_label=get_role_label(u.role),
            is_active=u.is_active,
            created_at=u.created_at.isoformat() if u.created_at else "",
        )
        for u in users
    ]


@router.post("/users")
def create_user(req: UserCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    if not has_permission(admin.role, "users", "create"):
        raise HTTPException(status_code=403, detail="无权限")

    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    existing_email = db.query(User).filter(User.email == req.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="邮箱已被使用")

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=get_password_hash(req.password),
        display_name=req.display_name or req.username,
        role=req.role if req.role in [r.value for r in Role] else "editor",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "message": "用户创建成功"}


@router.put("/users/{user_id}")
def update_user(user_id: str, req: UserUpdate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    if not has_permission(admin.role, "users", "update"):
        raise HTTPException(status_code=403, detail="无权限")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if req.email:
        existing = db.query(User).filter(User.email == req.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        user.email = req.email
    if req.display_name is not None:
        user.display_name = req.display_name
    if req.role and req.role in [r.value for r in Role]:
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active
    if req.password:
        user.hashed_password = get_password_hash(req.password)

    db.commit()
    return {"message": "用户更新成功"}


@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    if not has_permission(admin.role, "users", "delete"):
        raise HTTPException(status_code=403, detail="无权限")
    if str(admin.id) == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = False
    db.commit()
    return {"message": "用户已禁用"}


@router.get("/roles")
def list_roles(admin = Depends(require_admin)):
    return [
        {"value": r.value, "label": get_role_label(r.value)}
        for r in Role
    ]
