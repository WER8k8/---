from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.response import success_response
from app.models.product import Product
from app.models.im_routing_and_specs import MerchantIMRouting as MerchantImRouting
from app.models.shipping_timeline import ShippingTimeline


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/mobile"
ROUTE_TAGS = ["移动端API"]

router = APIRouter()


async def _mobile_product_view(
    product_id: str,
    request: Request,
    merchant_id: str = "default",
    db: Session = Depends(get_db)
):
    """
    移动端合并接口 - 一次性返回产品+IM路由+证书+物流时间线
    减少移动网络请求次数，提升弱网体验
    """
    # 1. 获取产品信息
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    # 2. 识别买家国家（从IP或请求参数）
    buyer_country = request.query_params.get("country", "US")  # 默认美国
    # 3. 获取IM路由配置
    # TODO [P2] Redis缓存优化（待高频查询瓶颈确认后实施）
    im_routings = db.query(MerchantImRouting).filter(
        MerchantImRouting.merchant_id == merchant_id,
        MerchantImRouting.country_code == buyer_country,
        MerchantImRouting.is_active == True
    ).order_by(MerchantImRouting.priority.asc()).all()
    # 默认路由（兜底）
    if not im_routings:
        im_channels = [{"channel_type": "whatsapp", "account_id": "", "prefilled_text": ""}]
    else:
        im_channels = [
            {
                "channel_type": r.channel_type,
                "account_id": r.account_id,
                "prefilled_text": r.prefilled_text or ""
            } for r in im_routings
        ]

    # 4. 获取物流时间线（根据买家国家）
    shipping = db.query(ShippingTimeline).filter(
        ShippingTimeline.merchant_id == merchant_id,
        ShippingTimeline.country_code == buyer_country,
        ShippingTimeline.is_active == True
    ).order_by(ShippingTimeline.sort_order.asc()).first()
    shipping_data = None
    if shipping:
        shipping_data = {
            "step_1": {"title": shipping.step_1_title, "desc": shipping.step_1_desc, "days": shipping.step_1_days},
            "step_2": {"title": shipping.step_2_title, "desc": shipping.step_2_desc, "days": shipping.step_2_days, "badge": shipping.step_2_badge},
            "step_3": {"title": shipping.step_3_title, "desc": shipping.step_3_desc, "days": shipping.step_3_days},
            "step_4": {"title": shipping.step_4_title, "desc": shipping.step_4_desc, "days": shipping.step_4_days}
        }

    # 5. 组装返回数据
    return success_response(data={
        "product": {
            "id": str(product.id),
            "name": product.name,
            "subtitle": product.subtitle,
            "description": product.description,
            "image_url": product.image_url,
            "meta_title": product.meta_title,
            "meta_description": product.meta_description,
            "specifications": product.specifications if isinstance(product.specifications, dict) else {}
        },
        "im_channels": im_channels,
        "shipping_timeline": shipping_data,
        "buyer_country": buyer_country
    })


@router.get("/product/{product_id}")
async def mobile_product_canonical(
    product_id: str,
    request: Request,
    merchant_id: str = "default",
    db: Session = Depends(get_db),
):
    """标准路径: GET /api/v1/mobile/product/{id}"""
    return await _mobile_product_view(product_id, request, merchant_id, db)


@router.get("/mobile/product/{product_id}")
async def mobile_product_legacy(
    product_id: str,
    request: Request,
    merchant_id: str = "default",
    db: Session = Depends(get_db),
):
    """兼容旧双前缀: GET /api/v1/mobile/mobile/product/{id}"""
    return await _mobile_product_view(product_id, request, merchant_id, db)
