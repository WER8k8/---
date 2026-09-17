# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""代理独立壳 API（UX-3a）— L2/L3 业绩与下级汇总。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.tenant import TenantPlan
from app.services.agent_aggregation_service import AgentAggregationService
from app.services.payment_service import PaymentService
from app.services.agent_portal_service import AgentPortalService
from app.services.traffic_analytics_service import TrafficAnalyticsService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/agent", tags=["代理壳"])


def _agent_only(user: User):
    """
    处理 _agent_only 相关业务逻辑。

    :param user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if user.role not in AgentAggregationService.AGENT_ROLES | {"admin", "super_admin"}:
        return error_response(403, "仅代理角色可访问")
    return None


@router.get("/dashboard")
def agent_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """业绩看板聚合（租户 + 财务台账 + 分润）。"""
    if err := _agent_only(current_user):
        return err
    svc = AgentPortalService(db)
    data = svc.build_dashboard(current_user)
    if not data:
        if current_user.role in {"admin", "super_admin"}:
            return success_response(data={
                "stats": {
                    "total_clients": 0,
                    "monthly_new_clients": 0,
                    "monthly_new_trend": 0,
                    "monthly_revenue": 0,
                    "monthly_revenue_count": 0,
                    "pending_commission": 0,
                    "estimated_settle_date": "—",
                },
                "subordinates": [],
                "recent_activities": [],
            })
        return error_response(404, "代理节点不存在")
    return success_response(data=data)


@router.get("/clients")
def agent_clients(
    search: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """代理辖区客户列表。"""
    if err := _agent_only(current_user):
        return err
    svc = AgentPortalService(db)
    return success_response(data=svc.list_clients(current_user, search=search, status=status, page=page, page_size=page_size))


@router.get("/payments")
def agent_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """代理辖区收款记录。"""
    if err := _agent_only(current_user):
        return err
    svc = AgentPortalService(db)
    return success_response(data=svc.list_payments(current_user, page=page, page_size=page_size))


@router.get("/trends")
def agent_trends(
    months: int = Query(6, ge=3, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """月度新增客户与收款趋势。"""
    if err := _agent_only(current_user):
        return err
    svc = AgentPortalService(db)
    return success_response(data=svc.monthly_trends(current_user, months=months))


class AccountOpeningRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=200)
    contact_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=6, max_length=30)
    email: Optional[str] = Field(None, max_length=200)
    package: str = Field("basic", max_length=50)
    remark: Optional[str] = Field(None, max_length=500)


class CollectPaymentRequest(BaseModel):
    tenant_id: str
    plan_id: Optional[str] = None
    package: Optional[str] = Field(None, description="套餐 code，与 plan_id 二选一")
    billing_cycle: str = Field("yearly", pattern="^(monthly|yearly)$")
    channel: str = Field("wechat", pattern="^(wechat|alipay)$")


@router.post("/account-opening")
def agent_account_opening(
    req: AccountOpeningRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """代理提交客户开户申请。"""
    if err := _agent_only(current_user):
        return err
    svc = AgentPortalService(db)
    try:
        data = svc.create_account_opening(
            current_user,
            req.model_dump(),
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=data, message="开户申请已提交")


@router.get("/plans")
def agent_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """代理壳 — 可选套餐（用于后台收款二维码）。"""
    if err := _agent_only(current_user):
        return err
    plans = (
        db.query(TenantPlan)
        .filter(TenantPlan.is_active.is_(True))
        .order_by(TenantPlan.price_yearly)
        .all()
    )
    return success_response(
        data=[
            {
                "id": p.id,
                "name": p.name,
                "code": p.code,
                "price_monthly": p.price_monthly,
                "price_yearly": p.price_yearly,
            }
            for p in plans
        ]
    )


@router.post("/collect-payment")
def agent_collect_payment(
    req: CollectPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """代理后台 — 为客户生成微信/支付宝 Native 收款二维码。"""
    if err := _agent_only(current_user):
        return err
    portal = AgentPortalService(db)
    try:
        tenant = portal.assert_tenant_in_scope(current_user, req.tenant_id)
    except ValueError as exc:
        return error_response(403, str(exc))

    plan_id = req.plan_id
    if not plan_id and req.package:
        plan = (
            db.query(TenantPlan)
            .filter(TenantPlan.code == req.package, TenantPlan.is_active.is_(True))
            .first()
        )
        if not plan:
            return error_response(400, "套餐不存在")
        plan_id = str(plan.id)
    if not plan_id:
        settings = tenant.settings or "{}"
        import json as _json
        try:
            pkg = _json.loads(settings).get("package_code", "basic")
        except (json.JSONDecodeError, ValueError):
            pkg = "basic"
        plan = (
            db.query(TenantPlan)
            .filter(TenantPlan.code == pkg, TenantPlan.is_active.is_(True))
            .first()
        )
        if not plan:
            return error_response(400, "请指定 plan_id 或 package")
        plan_id = str(plan.id)

    pay_svc = PaymentService(db)
    try:
        result = pay_svc.create_native_payment(
            tenant_id=str(tenant.id),
            plan_id=plan_id,
            billing_cycle=req.billing_cycle,
            current_user_id=str(current_user.id),
            channel=req.channel,
        )
    except ValueError as exc:
        return error_response(400, str(exc))

    order = result["order"]
    return success_response(
        data={
            "tenant_id": str(tenant.id),
            "tenant_name": tenant.name,
            "id": order.id,
            "order_no": order.order_no,
            "amount": order.amount,
            "subject": order.subject,
            "channel": order.channel,
            "code_url": result.get("code_url") or "",
            "mock": result.get("mock", False),
            "billing_cycle": req.billing_cycle,
        },
        message="收款二维码已生成",
    )


@router.get("/traffic-board")
def agent_traffic_board(
    period: str = "7d",
    node_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """代理辖区流量看板（含下级汇总维度）。"""
    if err := _agent_only(current_user):
        return err
    svc = AgentPortalService(db)
    target = node_id or svc.resolve_node_id(current_user)
    node_ids = TrafficAnalyticsService.agent_subtree_node_ids(db, target)
    traffic_svc = TrafficAnalyticsService(db)
    board = traffic_svc.build_board(
        period=period,
        agent_node_ids=node_ids,
        scope="agent",
    )
    board["node_id"] = target
    board["subtree_node_count"] = len(node_ids)
    children = AgentAggregationService.get_children(target, db) or []
    board["subordinate_traffic"] = []
    for child in children:
        cids = TrafficAnalyticsService.agent_subtree_node_ids(db, child["id"])
        child_board = traffic_svc.build_board(
            period=period, agent_node_ids=cids, scope="agent"
        )
        board["subordinate_traffic"].append(
            {
                "node_id": child["id"],
                "name": child["name"],
                "level": child["level"],
                **child_board["summary"],
            }
        )
    return success_response(data=board)


@router.get("/me")
def agent_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 agent_me 相关业务逻辑。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _agent_only(current_user):
        return err
    svc = AgentPortalService(db)
    return success_response(
        data={
            "role": current_user.role,
            "node_id": svc.resolve_node_id(current_user),
            "shell": "agent",
        }
    )
