"""API模块"""

from fastapi import APIRouter

from app.api.v1.routes import router as v1_router

router = APIRouter()


def register_routes():
    """整包导入完成后调用：先注册 v1 业务路由，再并入 api 聚合路由。"""
    from app.api.v1.routes import register_routes as _register_v1
    _register_v1()
    router.include_router(v1_router)
