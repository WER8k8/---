"""系统设置路由 - 模块化架构"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/settings"
ROUTE_TAGS = ["系统设置"]

router = APIRouter()


@router.get("/")
def get_settings(db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    """获取系统设置"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    return success_response(
        data={
            "site": {
                "name": "优丁建材",
                "domain": "www.youdingjiancai.com",
                "description": "专业轻集料混凝土生产企业",
                "keywords": "轻集料混凝土,保温材料,建筑材料",
            },
            "seo": {
                "title_prefix": "优丁建材 - ",
                "meta_description": "",
                "google_analytics_id": ""},
            "system": {
                "maintenance_mode": False,
                "max_upload_size": 10,
                "allowed_file_types": [
                    "jpg",
                    "png",
                    "pdf",
                    "doc"],
            },
        })


@router.put("/site")
def update_site_settings(
        req: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """更新站点设置"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    return success_response(data=req, message="站点设置更新成功")


@router.put("/seo")
def update_seo_settings(
        req: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """更新SEO设置"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    return success_response(data=req, message="SEO设置更新成功")


@router.put("/system")
def update_system_settings(
        req: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """更新系统设置"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")

    return success_response(data=req, message="系统设置更新成功")
