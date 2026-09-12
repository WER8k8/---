"""Admin BFF — 统一接入契约 (UAC)

分层边界：
  adapter/*   — 仅 HTTP 路由与参数校验
  bridge      — legacy APIResponse ↔ UAC 字段映射
  shell       — 角色 → 四壳
  menu_seeds  — 静态菜单数据
  menu_transform — 树结构 → UacMenuRoute
  user_context / tenant_lookup — 读模型组装
  plan_catalog — 套餐矩阵只读源
  schemas     — 对外 Pydantic 模型

前端（Vben / youding-admin-kit）只消费 /api/v1/admin-bff/*
内部可调用 legacy /auth/*，但不得泄漏 snake_case 给 Vben。
"""

from fastapi import APIRouter, Request

from app.api.v1.admin_bff.auth_adapter import bff_logout
from app.api.v1.admin_bff.auth_adapter import router as auth_router
from app.api.v1.admin_bff.dict_adapter import router as dict_router
from app.api.v1.admin_bff.menu_adapter import router as menu_router
from app.api.v1.admin_bff.lab_adapter import router as lab_router
from app.api.v1.admin_bff.plan_adapter import router as plan_router
from app.api.v1.admin_bff.user_adapter import router as user_router

router = APIRouter(prefix="/admin-bff", tags=["Admin BFF · UAC"])

router.include_router(auth_router, prefix="/auth")
router.include_router(user_router, prefix="/user")
router.include_router(menu_router, prefix="/menu")
router.include_router(dict_router, prefix="/dict")
router.include_router(plan_router, prefix="/plan")
router.include_router(lab_router, prefix="/lab")


@router.post("/logout")
def admin_bff_logout_alias(request: Request):
    """前端 bff.post('/logout') 调用 root 级路径；与 /admin-bff/auth/logout 等价。"""
    return bff_logout(request)
