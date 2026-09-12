"""用户管理路由"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.response import APIResponse, error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (ChangePasswordRequest, UserCreate,
                              UserListResponse, UserResponse, UserStatusUpdate,
                              UserUpdate)
from app.services.user_service import UserService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/users"
ROUTE_TAGS = ["用户管理"]

router = APIRouter(tags=["用户管理"])


@router.get("/", response_model=APIResponse[UserListResponse])
def list_users(
    page: int = 1,
    page_size: int = 20,
    role: str = None,
    search: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户列表（分页）"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = UserService(db)
    users, total = service.list_users(
        page=page, page_size=page_size, role=role, search=search)

    return success_response(
        data=UserListResponse(
            items=[
                UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size))


@router.get("/me", response_model=APIResponse[UserResponse])
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return success_response(data=UserResponse.model_validate(current_user))


@router.get("/logs", response_model=APIResponse)
def get_operation_logs(
    page: int = 1,
    page_size: int = 20,
    user_id: str = None,
    action: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取操作日志"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = UserService(db)
    logs, total = service.get_operation_logs(user_id=user_id, limit=page_size)
    return success_response(
        data={
            "items": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "detail": log.detail,
                    "created_at": log.created_at,
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/{user_id}", response_model=APIResponse[UserResponse])
def get_user(user_id: str, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    """获取单个用户信息"""
    if current_user.role not in ["admin",
                                 "super_admin"] and current_user.id != user_id:
        return error_response(403, "权限不足")

    service = UserService(db)
    user = service.get_user(user_id)
    if not user:
        return error_response(404, "用户不存在")

    return success_response(data=UserResponse.model_validate(user))


@router.post("/", response_model=APIResponse[UserResponse])
def create_user(
        user_data: UserCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """创建用户"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = UserService(db)
    try:
        user = service.create_user(user_data, created_by=current_user.id)
        return success_response(
            data=UserResponse.model_validate(user),
            message="用户创建成功")
    except ValueError as e:
        return error_response(400, str(e))


@router.put("/{user_id}", response_model=APIResponse[UserResponse])
def update_user(
        user_id: str,
        user_data: UserUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """更新用户信息"""
    if current_user.role not in ["admin",
                                 "super_admin"] and current_user.id != user_id:
        return error_response(403, "权限不足")

    service = UserService(db)
    try:
        user = service.update_user(
            user_id, user_data, updated_by=current_user.id)
        if not user:
            return error_response(404, "用户不存在")
        return success_response(
            data=UserResponse.model_validate(user),
            message="用户更新成功")
    except ValueError as e:
        return error_response(400, str(e))


@router.delete("/{user_id}", response_model=APIResponse)
def delete_user(user_id: str, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    """删除用户"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    if current_user.id == user_id:
        return error_response(400, "不能删除自己")

    service = UserService(db)
    if not service.delete_user(user_id, deleted_by=current_user.id):
        return error_response(404, "用户不存在")

    return success_response(message="用户删除成功")


@router.post("/{user_id}/change-password", response_model=APIResponse)
def change_password(
    user_id: str,
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改密码"""
    if current_user.role not in ["admin",
                                 "super_admin"] and current_user.id != user_id:
        return error_response(403, "权限不足")

    service = UserService(db)
    try:
        success = service.change_password(
            user_id,
            password_data.old_password,
            password_data.new_password)
        if not success:
            return error_response(400, "旧密码不正确")
        return success_response(message="密码修改成功")
    except ValueError as e:
        return error_response(400, str(e))


@router.post("/{user_id}/status", response_model=APIResponse[UserResponse])
def update_user_status(
    user_id: str,
    status_data: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新用户状态"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = UserService(db)
    user = service.update_user_status(user_id, status_data.is_active)
    if not user:
        return error_response(404, "用户不存在")

    return success_response(data=UserResponse.model_validate(user), message="状态更新成功")


@router.post("/batch-delete", response_model=APIResponse)
def batch_delete_users(
        user_ids: List[str],
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """批量删除用户"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    service = UserService(db)
    deleted = service.batch_delete(user_ids, deleted_by=current_user.id)
    return success_response(message=f"成功删除 {deleted} 个用户")
