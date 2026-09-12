"""数据分析路由 - 流量埋点与运营看板"""

import time
from collections import defaultdict
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User

# ── 埋点限流：200 次/小时/IP ──
_event_rate: dict[str, list[float]] = defaultdict(list)
_EVENT_LIMIT = 200
_EVENT_WINDOW = 3600


def _check_event_rate(ip: str) -> None:
    """
    处理 _check_event_rate 相关业务逻辑。

    :param ip: 入参 (str)。

    :return: 返回 None 类型的结果。

    :raises HTTPException: 当相应错误条件触发时抛出。
    """
    now = time.time()
    _event_rate[ip] = [t for t in _event_rate[ip] if now - t < _EVENT_WINDOW]
    if len(_event_rate[ip]) >= _EVENT_LIMIT:
        raise HTTPException(429, "请求过于频繁")
    _event_rate[ip].append(now)
from app.services.traffic_analytics_service import (
    TrafficAnalyticsService,
    resolve_tenant_id,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/analytics"
ROUTE_TAGS = ["数据分析"]

router = APIRouter()

BOARD_ROLES = frozenset(
    {"admin", "super_admin", "tenant_admin", "sales", "agent", "l2", "l3"}
)


class AnalyticsEventBody(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=64)
    product_id: Optional[str] = None
    merchant_id: Optional[str] = None
    tenant_id: Optional[str] = None
    agent_node_id: Optional[str] = None
    visitor_country: Optional[str] = None
    visitor_language: Optional[str] = None
    session_id: Optional[str] = None
    page_path: Optional[str] = None
    page_title: Optional[str] = None
    element_id: Optional[str] = None
    element_label: Optional[str] = None
    content_ref: Optional[str] = None
    meta: Optional[dict[str, Any]] = None


def _board_roles_ok(user: User) -> bool:
    """
    处理 _board_roles_ok 相关业务逻辑。

    :param user: 入参 (User)。

    :return: 返回 bool 类型的结果。
    """
    return user.role in BOARD_ROLES


def _content_stats(db: Session) -> dict[str, int]:
    """
    处理 _content_stats 相关业务逻辑。

    :param db: 入参 (Session)。

    :return: 返回 dict[str, int] 类型的结果。
    """
    from app.models.case_study import CaseStudy
    from app.models.content import ContentPage
    from app.models.product import Product
    return {
        "total_products": db.query(Product).filter(Product.is_active).count(),
        "total_cases": db.query(CaseStudy).filter(CaseStudy.is_active).count(),
        "total_pages": db.query(ContentPage).filter(ContentPage.is_active).count(),
    }


def _hot_products_from_board(
    board: dict[str, Any], db: Session, limit: int = 10
) -> list[dict[str, Any]]:
    """热门内容来自流量看板 top_content；无埋点则回退产品 view_count。"""
    items: list[dict[str, Any]] = []
    for c in board.get("top_content", [])[:limit]:
        ref = str(c.get("content_ref") or "")
        if not ref:
            continue
        name = ref
        if ref.startswith("product:"):
            name = ref.split(":", 1)[-1]
        elif ref.startswith("slug:"):
            name = ref.split(":", 1)[-1]
        items.append(
            {
                "id": ref,
                "name": name,
                "view_count": int(c.get("views") or 0),
                "inquiries": int(c.get("inquiries") or 0),
            }
        )
    if items:
        return items

    from app.models.product import Product
    rows = (
        db.query(Product)
        .filter(Product.is_active)
        .order_by(Product.view_count.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "view_count": int(p.view_count or 0),
            "slug": p.slug,
        }
        for p in rows
    ]


def _hot_cases_from_db(db: Session, limit: int = 5) -> list[dict[str, Any]]:
    """
    处理 _hot_cases_from_db 相关业务逻辑。

    :param db: 入参 (Session)。
    :param limit: 入参 (int)。

    :return: 返回 list[dict[str, Any]] 类型的结果。
    """
    from app.models.case_study import CaseStudy
    rows = (
        db.query(CaseStudy)
        .filter(CaseStudy.is_active)
        .order_by(CaseStudy.view_count.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(c.id),
            "name": c.project_name,
            "view_count": int(c.view_count or 0),
            "slug": c.slug,
        }
        for c in rows
    ]


@router.get("/site-context")
def analytics_site_context(
    host: str = Query("", description="当前页面 Host，用于解析租户"),
    merchant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """租户站埋点上下文（无需登录）：返回 tenant_id / 建议 merchant_id。"""
    tid = resolve_tenant_id(
        db, merchant_id=merchant_id, host=host or None
    )
    tenant_domain = None
    if tid:
        from app.models.tenant import Tenant
        t = db.query(Tenant).filter(Tenant.id == tid).first()
        if t:
            tenant_domain = t.domain
    return success_response(
        data={
            "tenant_id": tid,
            "merchant_id": merchant_id or tid,
            "tenant_domain": tenant_domain,
        }
    )


@router.post("/event")
def track_analytics_event(body: AnalyticsEventBody, request: Request, db: Session = Depends(get_db)):
    """访客行为埋点（无需登录）。限流 200 次/小时/IP。"""
    # ── 限流 ──
    client_ip = request.client.host if request.client else "unknown"
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        client_ip = fwd.split(",")[0].strip()
    _check_event_rate(client_ip)
    sid = (body.session_id or "anonymous").strip()[:64]
    if not sid:
        sid = "anonymous"
    svc = TrafficAnalyticsService(db)
    tid = body.tenant_id or resolve_tenant_id(
        db, merchant_id=body.merchant_id
    )
    try:
        row = svc.record_event(
            event_type=body.event_type,
            session_id=sid,
            tenant_id=tid,
            merchant_id=body.merchant_id,
            agent_node_id=body.agent_node_id,
            page_path=body.page_path,
            page_title=body.page_title,
            element_id=body.element_id,
            element_label=body.element_label,
            content_ref=body.content_ref,
            product_id=body.product_id,
            visitor_country=body.visitor_country,
            visitor_language=body.visitor_language,
            meta=body.meta,
        )
        return success_response(
            data={"accepted": True, "event_id": str(row.id), "event_type": body.event_type},
            message="ok",
        )
    except Exception as exc:
        db.rollback()
        return success_response(
            data={"accepted": False, "event_type": body.event_type, "error": str(exc)[:200]},
            message="ok",
        )


@router.get("/operations/traffic-board")
def operations_traffic_board(
    period: str = Query("7d"),
    tenant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """运营模块流量看板（与 /traffic-board 等价，按角色自动选域）。"""
    return get_traffic_board(
        period=period,
        tenant_id=tenant_id,
        db=db,
        current_user=current_user,
    )


@router.get("/traffic-board")
def get_traffic_board(
    period: str = Query("7d", description="1d / 7d / 30d / 90d"),
    tenant_id: Optional[str] = Query(None, description="超管可指定租户"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """运营流量看板（租户 / 平台管理员）。"""
    if not _board_roles_ok(current_user):
        return error_response(403, "权限不足")

    svc = TrafficAnalyticsService(db)
    if current_user.role in ("agent", "l2", "l3"):
        from app.services.agent_aggregation_service import AgentAggregationService
        node_id = AgentAggregationService.get_user_node_id(current_user.role, db)
        if not node_id:
            return error_response(404, "未配置代理节点")
        node_ids = TrafficAnalyticsService.agent_subtree_node_ids(db, node_id)
        board = svc.build_board(
            period=period, agent_node_ids=node_ids, scope="agent"
        )
        board["data_honesty"] = svc.build_data_honesty(board)
        board["node_id"] = node_id
        children = AgentAggregationService.get_children(node_id, db) or []
        # 批量查询所有子节点的子树 ID，再批量构建看板，避免 N+1
        node_child_map: dict[str, list[str]] = {}
        all_child_node_ids: list[str] = []
        for child in children:
            cids = TrafficAnalyticsService.agent_subtree_node_ids(db, child["id"])
            node_child_map[child["id"]] = cids
            all_child_node_ids.extend(cids)

        # 一次性构建平台级看板用于汇总
        board_data = svc.build_board(period=period, agent_node_ids=all_child_node_ids, scope="agent") if all_child_node_ids else {}
        board["subordinate_traffic"] = [
            {
                "node_id": child["id"],
                "name": child["name"],
                "level": child["level"],
                **board_data.get("summary", {}),
            }
            for child in children
        ]
        return success_response(data=board)

    if current_user.role in ("super_admin", "admin"):
        if tenant_id:
            data = svc.build_board_with_honesty(
                period=period, tenant_id=tenant_id, scope="tenant"
            )
        else:
            data = svc.build_platform_board(period=period)
        return success_response(data=data)

    tid = resolve_tenant_id(db, user=current_user)
    if not tid:
        return error_response(400, "未关联租户，无法查看流量看板")

    data = svc.build_board_with_honesty(period=period, tenant_id=tid, scope="tenant")
    return success_response(data=data)


@router.get("/traffic")
def get_traffic_data(
    period: str = "7d",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取流量趋势（兼容旧前端 analytics.vue）。"""
    if not _board_roles_ok(current_user):
        return error_response(403, "权限不足")

    svc = TrafficAnalyticsService(db)
    tid = resolve_tenant_id(db, user=current_user)
    if tid:
        board = svc.build_board(period=period, tenant_id=tid, scope="tenant")
    elif current_user.role in ("super_admin", "admin"):
        board = svc.build_platform_board(period=period)
    else:
        return success_response(data={"period": period, "data": []})

    data = [
        {
            "date": d["date"],
            "views": d["page_views"],
            "visitors": d["visitors"],
            "clicks": d["clicks"],
            "inquiries": d["inquiries"],
        }
        for d in board.get("daily", [])
    ]
    return success_response(data={"period": period, "data": data, "board": board})


@router.get("/")
def get_analytics_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """数据分析概览（接入真实流量摘要）。"""
    if not _board_roles_ok(current_user):
        return error_response(403, "权限不足")

    svc = TrafficAnalyticsService(db)
    tid = resolve_tenant_id(db, user=current_user)
    if tid:
        board = svc.build_board(period="7d", tenant_id=tid, scope="tenant")
        summary = board["summary"]
        return success_response(
            data={
                "overview": {
                    "total_visitors": summary["unique_visitors"],
                    "page_views": summary["page_views"],
                    "avg_session_duration": "—",
                },
                "top_pages": board.get("top_content", [])[:5],
                "traffic_sources": [],
                "conversions": {
                    "inquiries": summary["inquiries"],
                    "conversion_rate": summary["conversion_rate"],
                },
            }
        )

    board = svc.build_platform_board(period="7d")
    summary = board["summary"]
    return success_response(
        data={
            "overview": {
                "total_visitors": summary["unique_visitors"],
                "page_views": summary["page_views"],
                "avg_session_duration": "—",
            },
            "top_pages": board.get("top_content", [])[:5],
            "traffic_sources": [],
            "conversions": {
                "inquiries": summary["inquiries"],
                "conversion_rate": summary["conversion_rate"],
            },
            "active_tenants": board.get("active_tenants", 0),
        }
    )


@router.get("/dashboard")
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """仪表盘数据（含流量摘要）。"""
    if not _board_roles_ok(current_user):
        return error_response(403, "权限不足")

    from app.models.inquiry import Inquiry
    from app.services.finance_honesty import is_excluded_inquiry
    def _inq_stats(rows: list[Inquiry]) -> dict[str, int]:
        """
        处理 _inq_stats 相关业务逻辑。

        :param rows: 入参 (list[Inquiry])。

        :return: 返回 dict[str, int] 类型的结果。
        """
        real = [r for r in rows if not is_excluded_inquiry(r)]
        return {
            "total": len(real),
            "pending": sum(1 for r in real if r.status == "pending"),
            "contacted": sum(1 for r in real if r.status == "contacted"),
            "converted": sum(1 for r in real if r.status in ("converted", "won")),
        }

    svc = TrafficAnalyticsService(db)
    tid = resolve_tenant_id(db, user=current_user)
    traffic_summary: dict[str, Any] = {}
    board: dict[str, Any] = {}
    inq_stats = {"total": 0, "pending": 0, "contacted": 0, "converted": 0}
    content_stats = _content_stats(db)
    if tid:
        board = svc.build_board(period="7d", tenant_id=tid, scope="tenant")
        traffic_summary = board["summary"]
        base = db.query(Inquiry).filter(Inquiry.is_active, Inquiry.tenant_id == tid)
        inq_stats = _inq_stats(base.all())
    elif current_user.role in ("super_admin", "admin"):
        board = svc.build_platform_board(period="7d")
        traffic_summary = board["summary"]
        base = db.query(Inquiry).filter(Inquiry.is_active)
        inq_stats = _inq_stats(base.all())

    return success_response(
        data={
            "inquiries": inq_stats,
            "content": content_stats,
            "traffic": traffic_summary,
            "hot_products": _hot_products_from_board(board, db),
            "hot_cases": _hot_cases_from_db(db),
        }
    )


@router.get("/products")
def get_product_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_product_analytics）：处理相关业务逻辑并返回结果。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if not _board_roles_ok(current_user):
        return error_response(403, "权限不足")
    tid = resolve_tenant_id(db, user=current_user)
    if not tid:
        return success_response(data={"top_products": [], "category_stats": []})
    board = TrafficAnalyticsService(db).build_board(
        period="30d", tenant_id=tid, scope="tenant"
    )
    top = [
        {
            "id": c.get("content_ref"),
            "name": c.get("content_ref"),
            "view_count": c.get("views", 0),
            "inquiries": c.get("inquiries", 0),
        }
        for c in board.get("top_content", [])
        if c.get("content_ref")
    ]
    return success_response(data={"top_products": top, "category_stats": []})


@router.get("/export")
def export_analytics(
    request: Request,
    format: str = "csv",
    period: str = Query("7d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出流量日表 CSV（租户或平台）。"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    if not _board_roles_ok(current_user):
        return error_response(403, "权限不足")
    if format != "csv":
        return error_response(400, "仅支持 csv")

    from app.core.data_export_guard import assert_export_allowed
    svc = TrafficAnalyticsService(db)
    tid = resolve_tenant_id(db, user=current_user)
    if tid:
        board = svc.build_board(period=period, tenant_id=tid, scope="tenant")
        export_scope = "tenant"
    elif current_user.role in ("super_admin", "admin"):
        board = svc.build_platform_board(period=period)
        export_scope = "platform"
    else:
        return error_response(400, "无可用流量数据")

    daily = board.get("daily", [])
    assert_export_allowed(
        db,
        current_user,
        request,
        export_kind="traffic_analytics_csv",
        scope=export_scope,
        row_count=len(daily),
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "visitors", "page_views", "clicks", "inquiries"])
    for row in daily:
        writer.writerow(
            [
                row.get("date", ""),
                row.get("visitors", 0),
                row.get("page_views", 0),
                row.get("clicks", 0),
                row.get("inquiries", 0),
            ]
        )
    buf.seek(0)
    filename = f"traffic_{period}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/content-feedback")
def get_content_feedback(
    tenant_id: str = Query(..., description="租户 ID"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """内容发布闭环反馈摘要：收录率、排名变化、优秀/待优化内容。"""
    if not _board_roles_ok(current_user):
        return error_response(403, "权限不足")

    from app.services.content_feedback_loop import ContentFeedbackLoop
    loop = ContentFeedbackLoop(db)
    summary = loop.get_feedback_summary(tenant_id, days=days)
    return success_response(data=summary)


class RumBeaconBody(BaseModel):
    lcp_ms: Optional[float] = None
    inp_ms: Optional[float] = None
    cls: Optional[float] = None
    error_rate: Optional[float] = None
    page_path: Optional[str] = None
    tenant_id: Optional[str] = None


@router.post("/rum")
def ingest_rum_beacon(
    body: RumBeaconBody,
    request: Request,
    db: Session = Depends(get_db),
):
    """浏览器 RUM 信标（无需登录；供 Admin/租户站点上报 Core Web Vitals）。"""
    from app.services.rum_metrics_service import ingest_rum_sample
    data = ingest_rum_sample(
        db,
        lcp_ms=body.lcp_ms,
        inp_ms=body.inp_ms,
        cls=body.cls,
        error_rate=body.error_rate,
        page_path=body.page_path or request.headers.get("referer"),
        tenant_id=body.tenant_id,
    )
    return success_response(data=data, message="RUM 已记录")
