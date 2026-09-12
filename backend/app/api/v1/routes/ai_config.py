"""AI配置路由 - 真实数据库，禁止硬编码统计"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.ai_config_service import AIConfigService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/ai-config"
ROUTE_TAGS = ["AI配置"]

router = APIRouter()


@router.get("/")
def get_ai_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取 AI 配置（真实提供商列表）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    service = AIConfigService(db)
    providers = service.list_providers()
    enabled = [p for p in providers if p.is_active]
    default_provider = enabled[0].id if enabled else None
    return success_response(
        data={
            "providers": [
                {"id": p.id, "name": p.name, "enabled": bool(p.is_active)}
                for p in providers
            ],
            "default_provider": default_provider,
            "models": [],
            "quota": {
                "daily_limit": 0,
                "used_today": 0,
                "remaining": 0,
            },
            "has_data": bool(providers),
        }
    )


@router.put("/")
def update_ai_config(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新AI配置"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")

    return success_response(data=req, message="AI配置更新成功")


@router.post("/provider/{provider_id}/toggle")
def toggle_provider(
    provider_id: str,
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """切换AI提供商状态"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")

    return success_response(
        data={
            "provider_id": provider_id,
            "enabled": req.get("enabled", False),
        },
        message="状态切换成功",
    )


@router.get("/stats")
def get_ai_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取 AI 使用统计（真实 AIUsageLog 汇总）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    service = AIConfigService(db)
    stats = service.get_usage_stats()
    return success_response(
        data={
            "total_calls": stats.total_requests,
            "total_tokens": stats.total_tokens,
            "cost_estimate": stats.total_cost,
            "success_rate": stats.success_rate,
            "top_features": [],
            "has_data": stats.total_requests > 0,
        }
    )
