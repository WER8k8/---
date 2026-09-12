"""租户站 / 移动端公开 API（无需登录）。"""

import os

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import success_response
from app.core.database import get_db
from app.models.tenant import Tenant
from app.services.im_locale_service import resolve_im_channel, resolve_im_channels
from app.services.tenant_settings_service import hide_hub_backlink


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/mobile", tags=["移动端公开"])


def _default_merchant_id(raw: str) -> int:
    """执行 default_merchant_id 相关逻辑处理。
    
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if raw and raw != "default":
        try:
            return int(raw)
        except ValueError:
            pass
    return int(os.getenv("DEFAULT_MERCHANT_ID", "1"))


@router.get("/im-routing")
def mobile_im_routing(
    merchant_id: str = Query("default"),
    country_code: str = Query("US", min_length=2, max_length=2),
    language: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """StickyImBar / 产品页：按国家+语种返回 IM 渠道列表。"""
    mid = _default_merchant_id(merchant_id)
    channels = resolve_im_channels(
        db,
        merchant_id=mid,
        country_code=country_code,
        language=language,
    )
    payload = [c.to_dict() for c in channels]
    primary = payload[0] if payload else resolve_im_channel(
        db, merchant_id=mid, country_code=country_code, language=language
    ).to_dict()
    return success_response(
        data={
            "channels": payload,
            "primary": primary,
            "hide_social": False,
            "merchant_id": mid,
            "resolve_path": "/api/v1/im-routing/channels",
        }
    )


@router.get("/site-policy")
def mobile_site_policy(
    host: str = Query("", description="当前访问 Host"),
    tenant_domain: str | None = Query(None, description="租户 domain/slug"),
    db: Session = Depends(get_db),
):
    """P1-05：租户站是否隐藏总站友链。"""
    tenant = None
    key = (tenant_domain or host or "").strip().lower()
    if key:
        tenant = (
            db.query(Tenant)
            .filter(Tenant.domain == key, Tenant.is_active)
            .first()
        )
    return success_response(
        data={
            "hide_hub_backlink": hide_hub_backlink(tenant) if tenant else False,
            "tenant_found": tenant is not None,
        }
    )
