# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""智能物流与定价路由 - 模块化架构"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.order import Order
from app.models.user import User
from app.services.logistics_dashboard_service import build_logistics_overview
from app.services.logistics_router_service import (
    lbs_distance_estimate,
    plan_route,
)
from app.services.logistics_tracking_service import (
    fetch_tracking_payload,
    get_order_for_user,
    sync_order_from_tracking,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/logistics"
ROUTE_TAGS = ["智能物流定价"]

router = APIRouter()


@router.get("/track")
def track_shipment(
    tracking_number: str = Query(..., min_length=3, description="运单号"),
    carrier: str | None = Query(None, description="物流公司代码，可选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询物流轨迹（租户站 / 管理端）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "user"]:
        return error_response(403, "权限不足")
    number = tracking_number.strip()
    if not number:
        return error_response(400, "运单号不能为空")
    return success_response(data=fetch_tracking_payload(number, carrier))


@router.post("/orders/{order_id}/sync-tracking")
def sync_order_tracking(
    order_id: UUID,
    carrier: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按运单号拉取轨迹并回填订单状态/预计送达。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    order = get_order_for_user(db, order_id, current_user)
    if not order:
        return error_response(404, "订单不存在或无权访问")
    if not order.tracking_number:
        return error_response(400, "请先为订单填写运单号")
    try:
        data = sync_order_from_tracking(db, order, carrier=carrier)
    except ValueError as e:
        return error_response(400, str(e))
    return success_response(data=data, message="物流已同步至订单")


@router.get("/")
def get_logistics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取智能物流概览（P1-09：真实 orders 表聚合）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "user"]:
        return error_response(403, "权限不足")
    return success_response(data=build_logistics_overview(db, current_user))


@router.get("/lbs-routing")
def get_lbs_routing(
    origin_lat: float = None,
    origin_lng: float = None,
    dest_city: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """LBS测距与路径规划（无地图 API 时返回估算占位并明确标记 estimate）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    origin = {"lat": origin_lat, "lng": origin_lng} if origin_lat is not None or origin_lng is not None else None
    return success_response(data=lbs_distance_estimate(origin, dest_city))


@router.get("/routing-plan")
def get_routing_plan(
    origin: str = Query(..., min_length=1, description="始发地"),
    destination: str = Query(..., min_length=1, description="目的地"),
    weight_kg: float = Query(0, ge=0, description="重量 kg"),
    volume: float = Query(0, ge=0, description="体积 m3，可选"),
    urgency: str = Query("standard", description="standard / express"),
    preference: str = Query("balanced", description="balanced/cheapest/fastest/safest"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """多物流商比价 + 智能路由规划（§10）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    plan = plan_route(
        origin=origin, destination=destination,
        weight_kg=weight_kg, volume=volume,
        urgency=urgency, preference=preference,
    )
    return success_response(data=plan)


@router.get("/freight-calc")
def get_freight_calculation(
    distance_km: float = 0,
    weight_ton: float = 0,
    vehicle_type: str = "4-axle",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """运费精算（基础公式；未接第三方运价时返回估算值）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    rates = {
        "4-axle": 2.8,
        "6-axle": 3.2,
        "van": 4.5,
    }
    rate = rates.get(vehicle_type, rates["4-axle"])
    dist = max(float(distance_km or 0), 0)
    weight = max(float(weight_ton or 0), 0)
    base_freight = round(dist * weight * rate, 2)
    toll_fee = round(dist * 0.35, 2) if dist > 50 else 0
    surcharge = round(weight * 12, 2) if weight > 20 else 0
    total = round(base_freight + toll_fee + surcharge, 2)
    return success_response(
        data={
            "base_freight": base_freight,
            "toll_fee": toll_fee,
            "surcharge": surcharge,
            "total_freight": total,
            "vehicle_recommended": vehicle_type,
            "formula": "distance_km * weight_ton * rate + toll + surcharge",
            "inputs": {"distance_km": dist, "weight_ton": weight},
        }
    )


@router.get("/quotation")
def get_quotations(
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取报价单列表"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    return success_response(
        data={
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size})


@router.post("/quotation")
def create_quotation(
        req: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """生成报价单"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    return success_response(data=req, message="报价单生成成功")
