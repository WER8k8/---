"""国际询盘采集系统路由 - 独立于国内业务"""

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from app.core.config import settings
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.international import (
    InternationalCrawlLog, InternationalInquiry, InternationalTargetSite,
)
from app.models.user import User
from app.schemas.international import (
    InternationalInquiryResponse, InternationalInquiryUpdate,
    InternationalStats, InternationalTargetSiteCreate,
    InternationalTargetSiteResponse, InternationalTargetSiteUpdate,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/international"
ROUTE_TAGS = ["国际询盘采集"]

router = APIRouter()


def _week_ago_utc() -> datetime:
    """跨 SQLite / PostgreSQL 的「近 7 日」起点（勿用 func.make_interval）。"""
    return datetime.now(timezone.utc) - timedelta(days=7)


def _serialize_inquiry(row: InternationalInquiry) -> dict:
    """
    处理 _serialize_inquiry 相关业务逻辑。

    :param row: 入参 (InternationalInquiry)。

    :return: 返回 dict 类型的结果。
    """
    return InternationalInquiryResponse.model_validate(row).model_dump(mode="json")


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """验证爬虫webhook的HMAC签名"""
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


# ========== Webhook（爬虫回调，无用户认证） ==========

@router.post("/webhook")
async def receive_crawl_data(
    request: Request,
    x_signature: str = Header(None, alias="X-Signature"),
    x_timestamp: str = Header(None, alias="X-Timestamp"),
    db: Session = Depends(get_db),
):
    """接收爬虫加密数据（由Cloudflare Workers调用）"""
    secret = (settings.CRAWL_WEBHOOK_SECRET or "").strip()
    if not secret:
        return error_response(500, "Webhook密钥未配置")

    body = await request.body()
    if not x_signature:
        return error_response(403, "缺少 X-Signature")
    if not verify_webhook_signature(body, x_signature, secret):
        return error_response(403, "签名验证失败")

    # 防重放（5分钟窗口）
    if not x_timestamp:
        return error_response(403, "缺少 X-Timestamp")
    ts = int(x_timestamp)
    if abs(time.time() - ts) > 300:
        return error_response(403, "请求已过期")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return error_response(400, "无效的JSON数据")

    inquiry = InternationalInquiry(
        source_url=data.get("source_url", ""),
        source_title=data.get("source_title", ""),
        customer_name=data.get("customer_name"),
        email=data.get("email"),
        phone=data.get("phone"),
        company=data.get("company"),
        product_interest=data.get("product_interest"),
        product_model=data.get("product_model"),
        quantity=data.get("quantity"),
        budget=data.get("budget"),
        message=data.get("message"),
        inquiry_time=data.get("inquiry_time"),
        language=data.get("language"),
        region=data.get("region"),
        confidence=data.get("confidence", 0),
        raw_data=json.dumps(data.get("raw_fields", {}), ensure_ascii=False),
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return success_response(data={"id": inquiry.id}, message="询盘接收成功")


# ========== 询盘管理 ==========

@router.get("/inquiries")
def list_inquiries(
    page: int = 1,
    page_size: int = 20,
    region: str = Query(None),
    status: str = Query(None),
    search: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取国外询盘列表"""
    q = db.query(InternationalInquiry).filter(InternationalInquiry.is_active)
    if region:
        q = q.filter(InternationalInquiry.region == region)
    if status:
        q = q.filter(InternationalInquiry.status == status)
    if search:
        like = f"%{search}%"
        q = q.filter(
            InternationalInquiry.customer_name.ilike(like)
            | InternationalInquiry.email.ilike(like)
            | InternationalInquiry.phone.ilike(like)
            | InternationalInquiry.company.ilike(like)
            | InternationalInquiry.product_interest.ilike(like)
            | InternationalInquiry.message.ilike(like)
        )

    total = q.count()
    items = q.order_by(InternationalInquiry.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()

    return success_response(data={
        "items": [_serialize_inquiry(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/inquiries/{inquiry_id}")
def get_inquiry(
    inquiry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取询盘详情"""
    inquiry = db.query(InternationalInquiry).filter(
        InternationalInquiry.id == inquiry_id,
        InternationalInquiry.is_active,
    ).first()
    if not inquiry:
        return error_response(404, "询盘不存在")
    return success_response(data=inquiry)


@router.put("/inquiries/{inquiry_id}")
def update_inquiry(
    inquiry_id: str,
    body: InternationalInquiryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新询盘状态"""
    inquiry = db.query(InternationalInquiry).filter(
        InternationalInquiry.id == inquiry_id,
        InternationalInquiry.is_active,
    ).first()
    if not inquiry:
        return error_response(404, "询盘不存在")

    update_data = body.model_dump(exclude_none=True)
    for k, v in update_data.items():
        setattr(inquiry, k, v)
    db.commit()
    db.refresh(inquiry)
    return success_response(data=inquiry, message="询盘已更新")


# ========== 目标网站管理 ==========

@router.get("/sites")
def list_sites(
    page: int = 1,
    page_size: int = 50,
    region: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取目标网站列表"""
    q = db.query(InternationalTargetSite).filter(InternationalTargetSite.is_active)
    if region:
        q = q.filter(InternationalTargetSite.region == region)

    total = q.count()
    items = q.order_by(InternationalTargetSite.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    serialized = [
        InternationalTargetSiteResponse.model_validate(i).model_dump(mode="json")
        for i in items
    ]
    return success_response(data={"items": serialized, "total": total})


@router.post("/sites")
def create_site(
    body: InternationalTargetSiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加目标网站"""
    site = InternationalTargetSite(**body.model_dump())
    db.add(site)
    db.commit()
    db.refresh(site)
    data = InternationalTargetSiteResponse.model_validate(site).model_dump(mode="json")
    return success_response(data=data, message="目标网站已添加")


@router.put("/sites/{site_id}")
def update_site(
    site_id: str,
    body: InternationalTargetSiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新目标网站"""
    site = db.query(InternationalTargetSite).filter(
        InternationalTargetSite.id == site_id,
        InternationalTargetSite.is_active,
    ).first()
    if not site:
        return error_response(404, "目标网站不存在")

    for k, v in body.model_dump(exclude_none=True).items():
        setattr(site, k, v)
    db.commit()
    db.refresh(site)
    data = InternationalTargetSiteResponse.model_validate(site).model_dump(mode="json")
    return success_response(data=data, message="目标网站已更新")


@router.delete("/sites/{site_id}")
def delete_site(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """软删除目标网站"""
    site = db.query(InternationalTargetSite).filter(
        InternationalTargetSite.id == site_id,
        InternationalTargetSite.is_active,
    ).first()
    if not site:
        return error_response(404, "目标网站不存在")
    site.is_active = False
    site.status = "paused"
    db.commit()
    return success_response(message="目标网站已删除")


@router.post("/sites/{site_id}/scrape")
def trigger_site_scrape(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发采集（须配置爬虫 Worker / Webhook，禁止假成功）"""
    site = db.query(InternationalTargetSite).filter(
        InternationalTargetSite.id == site_id,
        InternationalTargetSite.is_active,
    ).first()
    if not site:
        return error_response(404, "目标网站不存在")

    secret = (settings.CRAWL_WEBHOOK_SECRET or "").strip()
    if not secret:
        return error_response(
            503,
            "国际采集 Worker 未配置：请部署爬虫 Sidecar 并设置 CRAWL_WEBHOOK_SECRET",
        )

    return error_response(
        501,
        "手动采集任务队列尚未接入，请通过已部署的国际爬虫 Worker 拉取",
    )


# ========== 统计 ==========

@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取采集统计"""
    total = db.query(InternationalInquiry).filter(InternationalInquiry.is_active).count()
    today = db.query(InternationalInquiry).filter(
        InternationalInquiry.is_active,
        cast(InternationalInquiry.created_at, Date) == func.current_date(),
    ).count()
    pending = db.query(InternationalInquiry).filter(
        InternationalInquiry.is_active,
        InternationalInquiry.status == "pending",
    ).count()
    this_week = db.query(InternationalInquiry).filter(
        InternationalInquiry.is_active,
        InternationalInquiry.created_at >= _week_ago_utc(),
    ).count()
    # 按地区统计
    by_region = (
        db.query(InternationalInquiry.region, func.count(InternationalInquiry.id))
        .filter(InternationalInquiry.is_active)
        .group_by(InternationalInquiry.region)
        .all()
    )
    # 按状态统计
    by_status = (
        db.query(InternationalInquiry.status, func.count(InternationalInquiry.id))
        .filter(InternationalInquiry.is_active)
        .group_by(InternationalInquiry.status)
        .all()
    )
    # 活跃站点数
    active_sites = db.query(InternationalTargetSite).filter(
        InternationalTargetSite.is_active,
        InternationalTargetSite.status == "active",
    ).count()
    return success_response(data={
        "total_inquiries": total,
        "today_inquiries": today,
        "pending_count": pending,
        "this_week_inquiries": this_week,
        "active_sites": active_sites,
        "by_region": {r: c for r, c in by_region},
        "by_status": {s: c for s, c in by_status},
    })


# ========== 采集日志 ==========

@router.get("/logs")
def list_crawl_logs(
    page: int = 1,
    page_size: int = 20,
    site_id: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取采集日志"""
    q = db.query(InternationalCrawlLog)
    if site_id:
        q = q.filter(InternationalCrawlLog.site_id == site_id)

    total = q.count()
    items = q.order_by(InternationalCrawlLog.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return success_response(data={"items": items, "total": total})
