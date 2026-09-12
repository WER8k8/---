"""A/B测试路由 - 模块化架构"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User

router = APIRouter()


@router.get("/")
def list_ab_tests(
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取A/B测试列表"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    return success_response(
        data={
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size})


@router.get("/{test_id}")
def get_ab_test(test_id: str, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    """获取单个A/B测试详情"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    return success_response(
        data={
            "id": test_id,
            "name": "",
            "status": "running",
            "variants": [],
            "results": {}})


@router.post("/")
def create_ab_test(req: dict, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    """创建A/B测试"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    return success_response(data=req, message="A/B测试创建成功")


@router.put("/{test_id}")
def update_ab_test(
        test_id: str,
        req: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """更新A/B测试"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    return success_response(data={**req, "id": test_id}, message="A/B测试更新成功")


@router.delete("/{test_id}")
def delete_ab_test(
        test_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """删除A/B测试"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    return success_response(message="A/B测试删除成功")


@router.post("/{test_id}/start")
def start_ab_test(test_id: str, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    """启动A/B测试"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    return success_response(
        data={
            "test_id": test_id,
            "status": "running"},
        message="A/B测试已启动")


@router.post("/{test_id}/stop")
def stop_ab_test(test_id: str, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    """停止A/B测试"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    return success_response(
        data={
            "test_id": test_id,
            "status": "stopped"},
        message="A/B测试已停止")
