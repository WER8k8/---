"""
商家IM路由配置 API路由

提供IM渠道配置的CRUD接口，以及根据IP国家代码动态返回IM渠道的接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.im_routing_and_specs import MerchantIMRouting, BuildingMaterialSpec
from app.schemas.im_routing_and_specs import (
    MerchantIMRoutingCreate,
    MerchantIMRoutingUpdate,
    MerchantIMRoutingResponse,
    IMChannelResponse,
)
from app.core.security import get_current_user
from app.core.response import success_response
from app.models.user import User
from app.services.im_locale_service import (
    list_supported_languages,
    resolve_im_channel,
    resolve_im_channels,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/im-routing"
ROUTE_TAGS = ["IM路由配置"]

router = APIRouter(tags=["IM路由配置"])


@router.post("/", response_model=MerchantIMRoutingResponse, status_code=201)
def create_im_routing(
    routing: MerchantIMRoutingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建IM路由配置"""
    db_routing = MerchantIMRouting(
        merchant_id=current_user.id,  # 使用当前登录用户ID
        country_code=routing.country_code.upper(),
        channel_type=routing.channel_type,
        account_id=routing.account_id,
        prefilled_text=routing.prefilled_text,
        is_active=routing.is_active
    )
    db.add(db_routing)
    db.commit()
    db.refresh(db_routing)
    return db_routing


@router.get("/", response_model=List[MerchantIMRoutingResponse])
def list_im_routings(
    country_code: Optional[str] = Query(None, description="按国家代码过滤"),
    is_active: Optional[bool] = Query(None, description="按是否启用过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出当前用户的IM路由配置"""
    query = db.query(MerchantIMRouting).filter(
        MerchantIMRouting.merchant_id == current_user.id
    )
    if country_code:
        query = query.filter(MerchantIMRouting.country_code == country_code.upper())
    if is_active is not None:
        query = query.filter(MerchantIMRouting.is_active == is_active)
    
    return query.order_by(MerchantIMRouting.country_code).all()


@router.get("/languages")
def list_im_languages():
    """12 语种列表（全球化 IM 文案）。"""
    return success_response(data={"languages": list_supported_languages()})


@router.get("/channels")
def resolve_visitor_im_channels(
    merchant_id: int = Query(..., description="商家ID"),
    country_code: str = Query(..., min_length=2, max_length=2),
    language: str | None = Query(None, description="ISO 639-1，如 zh/en/ar"),
    db: Session = Depends(get_db),
):
    """P1-01：与 /mobile/im-routing 同源的统一多通道解析。"""
    channels = resolve_im_channels(
        db,
        merchant_id=merchant_id,
        country_code=country_code,
        language=language,
    )
    items = [c.to_dict() for c in channels]
    return success_response(
        data={
            "channels": items,
            "primary": items[0] if items else None,
        }
    )


@router.get("/resolve")
def resolve_visitor_im_channel(
    merchant_id: int = Query(..., description="商家ID"),
    country_code: str = Query(..., min_length=2, max_length=2),
    language: str | None = Query(None, description="ISO 639-1，如 zh/en/ar"),
    db: Session = Depends(get_db),
):
    """按国家+语种解析 IM 渠道（Nuxt 访客站调用，无需登录）。"""
    resolved = resolve_im_channel(
        db,
        merchant_id=merchant_id,
        country_code=country_code,
        language=language,
    )
    return success_response(data=resolved.to_dict())


@router.get("/channel/{country_code}", response_model=IMChannelResponse)
def get_im_channel_by_country(
    country_code: str,
    merchant_id: int = Query(..., description="商家ID"),
    request: Request = None,  # 用于获取访客IP（可选）
    db: Session = Depends(get_db)
):
    """根据商家ID和国家代码动态返回IM渠道配置
    
    这是核心接口，供Nuxt 3服务端调用。
    Nuxt 3根据访客IP解析国家代码后，调用此接口获取对应的IM渠道。
    """
    routing = db.query(MerchantIMRouting).filter(
        MerchantIMRouting.merchant_id == merchant_id,
        MerchantIMRouting.country_code == country_code.upper(),
        MerchantIMRouting.is_active == True
    ).first()
    if not routing:
        # 返回默认配置（Live Chat）
        return IMChannelResponse(
            channel_type="live_chat",
            account_id="",
            prefilled_text="Hello! How can I help you?",
            im_link="#contact",
            display_text="Live Chat"
        )
    
    # 生成IM链接
    im_link = generate_im_link(routing.channel_type, routing.account_id)
    display_text = get_display_text(routing.channel_type, country_code)
    return IMChannelResponse(
        channel_type=routing.channel_type,
        account_id=routing.account_id,
        prefilled_text=routing.prefilled_text,
        im_link=im_link,
        display_text=display_text
    )


def generate_im_link(channel_type: str, account_id: str) -> str:
    """生成IM渠道链接"""
    if channel_type == "whatsapp":
        return f"https://wa.me/{account_id}"
    elif channel_type == "telegram":
        return f"https://t.me/{account_id}"
    elif channel_type == "line":
        return f"https://line.me/ti/p/{account_id}"
    elif channel_type == "zalo":
        return f"https://zalo.me/{account_id}"
    elif channel_type == "live_chat":
        return "#contact"
    elif channel_type == "form":
        return "#inquiry-form"
    else:
        return "#"


def get_display_text(channel_type: str, country_code: str) -> str:
    """根据渠道类型和国家代码返回显示文本"""
    channel_names = {
        "whatsapp": "Chat on WhatsApp",
        "telegram": "Chat on Telegram",
        "line": "Chat on LINE",
        "zalo": "Chat on Zalo",
        "live_chat": "Live Chat",
        "form": "Send Inquiry"
    }
    # 可以根据country_code返回本地语言文本（未来扩展）
    return channel_names.get(channel_type, "Contact Us")


@router.get("/{routing_id}", response_model=MerchantIMRoutingResponse)
def get_im_routing(
    routing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个IM路由配置详情"""
    routing = (
        db.query(MerchantIMRouting)
        .filter(
            MerchantIMRouting.id == routing_id,
            MerchantIMRouting.merchant_id == current_user.id,
        )
        .first()
    )
    if not routing:
        raise HTTPException(status_code=404, detail="IM路由配置不存在")
    return routing


@router.put("/{routing_id}", response_model=MerchantIMRoutingResponse)
def update_im_routing(
    routing_id: int,
    routing_update: MerchantIMRoutingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新IM路由配置"""
    routing = (
        db.query(MerchantIMRouting)
        .filter(
            MerchantIMRouting.id == routing_id,
            MerchantIMRouting.merchant_id == current_user.id,
        )
        .first()
    )
    if not routing:
        raise HTTPException(status_code=404, detail="IM路由配置不存在")
    update_data = routing_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(routing, field, value)
    db.commit()
    db.refresh(routing)
    return routing


@router.delete("/{routing_id}", status_code=204)
def delete_im_routing(
    routing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除IM路由配置"""
    routing = (
        db.query(MerchantIMRouting)
        .filter(
            MerchantIMRouting.id == routing_id,
            MerchantIMRouting.merchant_id == current_user.id,
        )
        .first()
    )
    if not routing:
        raise HTTPException(status_code=404, detail="IM路由配置不存在")
    db.delete(routing)
    db.commit()
