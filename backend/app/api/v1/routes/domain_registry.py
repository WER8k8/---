"""领域注册状态 API — FIX-31

提供领域模块注册信息的查询端点。
"""
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.core.response import success_response
from app.domains import DOMAIN_REGISTRY, list_domains

router = APIRouter(prefix="/domains", tags=["领域注册"])


@router.get("")
async def get_domain_registry(current_user=Depends(get_current_user)):
    """获取领域注册状态。返回所有已注册领域的元数据。"""
    domains = []
    for name, domain_cls in DOMAIN_REGISTRY.items():
        instance = domain_cls()
        domains.append(instance.get_facade())

    return success_response(data={
        "total": len(domains),
        "domains": domains,
        "architecture": "modular-monolith",
        "migration_status": {
            "lead": "complete",      # 获客引擎 - 已完成迁移
            "auth": "stub",          # 认证授权 - 待迁移
            "tenant": "stub",        # 租户管理 - 待迁移
            "product": "stub",       # 产品管理 - 待迁移
            "content": "stub",       # 内容管理 - 待迁移
            "inquiry": "stub",       # 询盘管理 - 待迁移
            "seo": "stub",           # SEO优化 - 待迁移
            "ai": "stub",            # AI智能 - 待迁移
            "payment": "stub",       # 支付财务 - 待迁移
            "system": "stub",        # 系统管理 - 待迁移
            "public": "stub",        # 公开API - 待迁移
        },
    })