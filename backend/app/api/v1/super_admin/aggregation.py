"""超管数据中心 — 代理层级 + 全平台流量汇总。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.inquiry import Inquiry
from app.models.site_analytics import SiteAnalyticsEvent
from app.models.user import User
from app.repositories.tenant_repository import TenantRepository
from app.services.agent_aggregation_service import AgentAggregationService
from app.services.finance_honesty import is_excluded_inquiry, is_probe_analytics_row
from app.services.finance_service import FinanceService
from app.services.traffic_analytics_service import TrafficAnalyticsService

router = APIRouter()


def _require_super(user: User):
    """_require_super。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    if user.role not in ("super_admin", "admin"):
        return error_response(403, "仅超级管理员可访问")
    return None


def _map_period(raw: str) -> str:
    """前端数据中心 period 与流量看板 period 对齐。"""
    return {"month": "30d", "quarter": "90d", "year": "90d"}.get(raw, raw)


def _tree_node_to_ui(node: dict) -> dict:
    """_tree_node_to_ui。

    参数说明：
    :param node: 参数 node
    :return: 返回处理结果。
    """
    stats = node.get("stats") or {}
    monthly = float(stats.get("monthly_revenue") or 0)
    return {
        "name": str(node.get("id") or node.get("name") or "node"),
        "label": str(node.get("name") or node.get("id") or "—"),
        "level": str(node.get("level") or "l0"),
        "clientCount": int(stats.get("total_clients") or 0),
        "revenue": f"{monthly:.2f}" if monthly > 0 else "0",
        "children": [
            _tree_node_to_ui(child) for child in (node.get("children") or [])
        ],
    }


def _tree_to_ui(tree: dict | list | None) -> list[dict]:
    """_tree_to_ui。

    参数说明：
    :param tree: 参数 tree
    :return: 返回处理结果。
    """
    if not tree:
        return []
    if isinstance(tree, list):
        return [_tree_node_to_ui(node) for node in tree]
    if tree.get("has_data") is False and not tree.get("children"):
        return []
    return [_tree_node_to_ui(tree)]


def _build_data_honesty(db: Session, traffic: dict) -> dict:
    """_build_data_honesty。

    参数说明：
    :param db: 参数 db
    :param traffic: 参数 traffic
    :return: 返回处理结果。
    """
    inquiries_total = db.query(Inquiry).filter(Inquiry.is_active.is_(True)).count()
    excluded_inquiries = sum(
        1 for i in db.query(Inquiry).filter(Inquiry.is_active.is_(True)).all()
        if is_excluded_inquiry(i)
    )
    events_total = db.query(SiteAnalyticsEvent).count()
    excluded_events = sum(
        1
        for e in db.query(SiteAnalyticsEvent).all()
        if is_probe_analytics_row(session_id=e.session_id, meta_json=e.meta_json)
        or not e.tenant_id
    )
    summary = traffic.get("summary") or {}
    has_production_activity = any(
        int(summary.get(key) or 0) > 0
        for key in ("unique_visitors", "page_views", "inquiries", "total_clicks")
    )
    return {
        "has_production_activity": has_production_activity,
        "excluded_inquiries": excluded_inquiries,
        "excluded_analytics_events": excluded_events,
        "raw_inquiries": inquiries_total,
        "raw_analytics_events": events_total,
        "notes": [
            "已排除 dev_seed / E2E 询盘与无租户归属的探针埋点",
            "mock_pay 渠道实收不计入本月营收",
        ],
    }


@router.get("/aggregation")
def super_admin_aggregation(
    period: str = Query("7d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """全平台汇总（兼容 admin aggregation.vue）。"""
    if err := _require_super(current_user):
        return err

    traffic_period = _map_period(period)
    traffic = TrafficAnalyticsService(db).build_platform_board(period=traffic_period)
    tree = AgentAggregationService.get_full_tree(db) or {"has_data": False, "children": []}
    tenant_stats = TenantRepository(db).get_stats()
    finance = FinanceService(db)
    month_rev_cents = finance.revenue_this_month_cents()
    if month_rev_cents <= 0:
        month_rev_cents = int(tenant_stats.get("monthly_revenue") or 0)
    daily_revenue = finance.revenue_by_day(
        days={"7d": 7, "30d": 30, "90d": 90}.get(traffic_period, 7)
    )
    level_summary = []
    for level in ("l1", "l2", "l3", "l4", "l5"):
        nodes = AgentAggregationService.get_level_summary(db, level)
        if not nodes:
            continue
        total_clients = sum(n["stats"]["total_clients"] for n in nodes)
        monthly_revenue = sum(n["stats"]["monthly_revenue"] for n in nodes)
        level_summary.append(
            {
                "id": level,
                "name": {
                    "l1": "全国总代",
                    "l2": "区域代理",
                    "l3": "市级代理",
                    "l4": "区县代理",
                    "l5": "终端代理",
                }.get(level, level),
                "count": len(nodes),
                "clientCount": total_clients,
                "revenue": round(monthly_revenue, 2),
            }
        )

    monthly_revenue_label = (
        f"{month_rev_cents / 100:.2f}" if month_rev_cents > 0 else "—"
    )
    platform_stats = {
        "totalVisitors": traffic["summary"]["unique_visitors"],
        "monthlyNewTenants": tenant_stats.get("new_tenants_this_month", 0),
        "monthlyRevenue": monthly_revenue_label,
        "activeTenants": traffic.get("active_tenants", 0),
        "expiringSoon": tenant_stats.get("expiring_soon", 0),
        "arr": "—",
        "pageViews": traffic["summary"]["page_views"],
        "totalClicks": traffic["summary"]["total_clicks"],
        "conversionRate": traffic["summary"]["conversion_rate"],
        "revenue_data_source": "ledger" if month_rev_cents > 0 else "empty",
    }
    province_stats = [
        {
            "province": row.get("node_name", ""),
            "clientCount": row.get("unique_visitors", 0),
            "inquiryCount": row.get("inquiries", 0),
            "pageViews": row.get("page_views", 0),
            "revenue": "—",
            "metric_label": "独立访客",
        }
        for row in traffic.get("by_agent_node", [])[:12]
    ]
    monthly_trend = [
        {
            "month": d["date"][5:],
            "monthLabel": d["date"],
            "visitors": d.get("visitors", 0),
            "inquiries": d.get("inquiries", 0),
            "pageViews": d.get("page_views", 0),
            "revenue_cents": daily_revenue.get(d["date"], 0),
        }
        for d in traffic.get("daily", [])
    ]
    data_honesty = _build_data_honesty(db, traffic)
    return success_response(
        data={
            "level_summary": level_summary,
            "platform_stats": platform_stats,
            "province_stats": province_stats,
            "tree_data": _tree_to_ui(tree),
            "monthly_trend": monthly_trend,
            "traffic": traffic,
            "data_honesty": data_honesty,
        }
    )


@router.get("/traffic-board")
def super_admin_traffic_board(
    period: str = Query("7d"),
    tenant_id: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """super_admin_traffic_board。

    参数说明：
    :param period: 参数 period
    :param tenant_id: 参数 tenant_id
    :param db: 参数 db
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    if err := _require_super(current_user):
        return err
    svc = TrafficAnalyticsService(db)
    if tenant_id:
        data = svc.build_board(period=period, tenant_id=tenant_id, scope="tenant")
    else:
        data = svc.build_platform_board(period=period)
    return success_response(data=data)
