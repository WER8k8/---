"""Agent 代理壳 BFF — 首屏聚合（T-ARCH-2）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.agent_portal_service import AgentPortalService
from app.services.bff_cache_service import bff_cache_key, cached_bff


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/bff/agent", tags=["Agent BFF"])

_AGENT_ROLES = frozenset({"agent", "sales", "l2", "l3"})


@router.get("/summary")
def agent_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """代理首页：佣金、客户数、待开户摘要（目标 <200ms）。"""
    if current_user.role not in _AGENT_ROLES:
        return error_response(403, "权限不足")

    svc = AgentPortalService(db)
    node_id = svc.resolve_node_id(current_user)
    key = bff_cache_key("agent", "summary", node_id)
    def _build() -> dict:
        """
        处理 _build 相关业务逻辑。

        :return: 返回 dict 类型的结果。
        """
        dash = svc.build_dashboard(current_user) or {}
        stats = dash.get("stats") or {}
        return {
            "node_id": node_id,
            "stats": {
                "total_clients": stats.get("total_clients", 0),
                "monthly_new_clients": stats.get("monthly_new_clients", 0),
                "pending_commission_cents": stats.get("pending_commission_cents", 0),
                "monthly_revenue_cents": stats.get("monthly_revenue_cents", 0),
                "estimated_settle_date": stats.get("estimated_settle_date"),
                "data_source": stats.get("data_source", "empty"),
            },
            "subordinates_count": len(dash.get("subordinates") or []),
        }

    return success_response(data=cached_bff(key, ttl_sec=45, builder=_build))
