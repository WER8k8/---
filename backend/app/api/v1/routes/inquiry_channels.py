"""企微 / 抖音等 IM 渠道 webhook（七步⑤ 框架入口）。"""

import json
import os

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.core.tenant_access import deny_unless_module
from app.db.session import get_db
from app.models.user import User
from app.services.im_channel_webhook_service import ingest_channel_inquiry


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/inquiries/channels", tags=["询盘渠道"])

_CHANNEL_META = (
    {"id": "wecom", "label": "企业微信", "path": "/wecom", "source_channel": "wecom_inquiry"},
    {"id": "douyin", "label": "抖音私信", "path": "/douyin", "source_channel": "douyin_inquiry"},
)


class ChannelInquiryBody(BaseModel):
    name: str = Field(default="渠道访客", max_length=120)
    phone: str = Field(..., min_length=6, max_length=20)
    message: str = Field(default="", max_length=4000)
    merchant_id: str | None = None


def _verify_webhook(secret_header: str | None) -> bool:
    """
    处理 _verify_webhook 相关业务逻辑。

    :param secret_header: 入参 (str | None)。

    :return: 返回 bool 类型的结果。
    """
    expected = os.getenv("INQUIRY_WEBHOOK_SECRET", "").strip()
    if not expected:
        return True
    return (secret_header or "").strip() == expected


def _api_base_url() -> str:
    """
    处理 _api_base_url 相关业务逻辑。

    :return: 返回 str 类型的结果。
    """
    base = os.getenv("PUBLIC_API_BASE", settings.SITE_URL.rstrip("/")).rstrip("/")
    return f"{base}/api/v1"


@router.get("/config")
def inquiry_channel_config(
    current_user: User = Depends(get_current_user),
):
    """MOD-02 · 企微/抖音 webhook 接入手册（只读，不含密钥明文）。"""
    denied = deny_unless_module(current_user, "inquiries", "read")
    if denied and (current_user.role or "") != "user":
        return denied
    secret = os.getenv("INQUIRY_WEBHOOK_SECRET", "").strip()
    api_base = _api_base_url()
    sample = {
        "name": "渠道访客",
        "phone": "13800138000",
        "message": "想了解岩棉板出口报价",
        "merchant_id": None,
    }
    sample_json = json.dumps(sample, ensure_ascii=False)
    channels = []
    for ch in _CHANNEL_META:
        url = f"{api_base}/inquiries/channels{ch['path']}"
        headers = "-H 'Content-Type: application/json'"
        if secret:
            headers += " -H 'X-Inquiry-Webhook-Secret: <YOUR_SECRET>'"
        curl = f"curl -X POST '{url}' {headers} -d '{sample_json}'"
        channels.append(
            {
                **ch,
                "url": url,
                "method": "POST",
                "curl_example": curl,
            }
        )
    return success_response(
        data={
            "secret_configured": bool(secret),
            "secret_header": "X-Inquiry-Webhook-Secret",
            "sample_body": sample,
            "channels": channels,
            "ops_note": "生产环境请在服务器 .env 设置 INQUIRY_WEBHOOK_SECRET 与 PUBLIC_API_BASE",
        }
    )


@router.post("/wecom")
def wecom_inquiry_webhook(
    body: ChannelInquiryBody,
    db: Session = Depends(get_db),
    x_inquiry_webhook_secret: str | None = Header(None, alias="X-Inquiry-Webhook-Secret"),
):
    """企业微信客服/私信转询盘（配置 INQUIRY_WEBHOOK_SECRET 验签）。"""
    if not _verify_webhook(x_inquiry_webhook_secret):
        return error_response(403, "webhook 密钥无效")
    data = ingest_channel_inquiry(
        db,
        channel="wecom_inquiry",
        name=body.name,
        phone=body.phone,
        message=body.message,
        merchant_id=body.merchant_id,
    )
    return success_response(data=data, message="企微询盘已入库")


@router.post("/douyin")
def douyin_inquiry_webhook(
    body: ChannelInquiryBody,
    db: Session = Depends(get_db),
    x_inquiry_webhook_secret: str | None = Header(None, alias="X-Inquiry-Webhook-Secret"),
):
    """抖音私信转询盘。"""
    if not _verify_webhook(x_inquiry_webhook_secret):
        return error_response(403, "webhook 密钥无效")
    data = ingest_channel_inquiry(
        db,
        channel="douyin_inquiry",
        name=body.name,
        phone=body.phone,
        message=body.message,
        merchant_id=body.merchant_id,
    )
    return success_response(data=data, message="抖音询盘已入库")
