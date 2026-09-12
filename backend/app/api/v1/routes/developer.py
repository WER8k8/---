"""开发者生态与低代码路由 - 模块化架构"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/developer"
ROUTE_TAGS = ["开发者生态"]

router = APIRouter()


@router.get("/")
def get_developer_overview(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取开发者生态概览"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")
    return success_response(
        data={
            "api_endpoints": 0,
            "api_calls_today": 0,
            "sdk_downloads": 0,
            "registered_plugins": 0})


@router.get("/sdk")
def get_sdk_list(db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    """获取SDK列表"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")
    return success_response(
        data={
            "sdks": [
                {"language": "Python", "version": "1.0.0", "download_url": ""},
                {"language": "JavaScript", "version": "1.0.0", "download_url": ""},
                {"language": "Java", "version": "1.0.0", "download_url": ""},
            ]
        }
    )


@router.get("/low-code")
def get_low_code_status(db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    """获取低代码平台状态"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")
    return success_response(
        data={
            "available_components": 0,
            "templates": [],
            "saved_pages": 0})


@router.get("/plugins")
def get_plugin_market(
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取插件市场"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")
    return success_response(
        data={
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size})
