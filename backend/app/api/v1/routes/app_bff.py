# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""出海计 App BFF — 聚合首页数据。"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.cache import async_cache_decorator
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.app_device import AppDevice
from app.services.push_notification_service import (
    fcm_enabled,
    notify_inquiry_pending,
    notify_publish_failed,
)
from app.services.bff_cache_service import bff_cache_key, cached_bff
from app.services.client_today_service import build_today_payload
from app.services.finance_honesty import count_real_inquiries
from app.services.ubrain import ubrain_orchestrator
from app.services.ubrain.chat_task_service import UBrainChatTaskError, run_chat_task
from app.models.inquiry import Inquiry
from app.models.product import Product
from app.models.tenant import Tenant, UserTenant
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/app/v1", tags=["出海计App"])


def _tenant(db: Session, user: User):
    """
    处理 _tenant 相关业务逻辑。

    :param db: 入参 (Session)。
    :param user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    link = db.query(UserTenant).filter(
        UserTenant.user_id == user.id,
        UserTenant.is_active,
    ).first()
    if not link:
        return None, error_response(403, "未关联租户")
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant:
        return None, error_response(404, "租户不存在")
    return tenant, None


@router.get("/home")
def app_home(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 app_home 相关业务逻辑。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant, err = _tenant(db, current_user)
    if err:
        return err

    tid = str(tenant.id)
    key = bff_cache_key("app", "home", tid)
    def _build() -> dict:
        """
        处理 _build 相关业务逻辑。

        :return: 返回 dict 类型的结果。
        """
        pending = count_real_inquiries(db, tenant_id=tid, status="pending")
        products = db.query(Product).filter(Product.is_active).count()
        brand_name = tenant.name or "出海计"
        today = build_today_payload(db=db, tenant=tenant, pending_inquiries=pending)
        return {
            "brand": {"name": brand_name},
            "today_one_thing": today["today_one_thing"],
            "blue_ocean_hint": today["blue_ocean_hint"],
            "stats": {
                "pending_inquiries": pending,
                "products": products,
            },
            "quick_actions": [
                {"id": "assistant", "label": "问优丁助手", "path": "/client/assistant"},
                {"id": "inquiries", "label": "询盘", "path": "/client/inquiries"},
                {"id": "content", "label": "发布", "path": "/client/content"},
            ],
        }

    return success_response(data=cached_bff(key, ttl_sec=45, builder=_build))


class DeviceRegisterRequest(BaseModel):
    device_token: str = Field(..., min_length=8, max_length=512)
    platform: str = Field(default="web", pattern="^(ios|android|web)$")
    app_version: str | None = None


@router.post("/devices/register")
def register_device(
    body: DeviceRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """注册 Push 设备（APP-1b 前置；推送通道待接 FCM/APNs）。"""
    tenant, err = _tenant(db, current_user)
    tenant_id = str(tenant.id) if tenant else None
    existing = (
        db.query(AppDevice)
        .filter(
            AppDevice.user_id == str(current_user.id),
            AppDevice.device_token == body.device_token,
        )
        .first()
    )
    if existing:
        existing.platform = body.platform
        existing.app_version = body.app_version
        existing.tenant_id = tenant_id
        db.commit()
        return success_response(data={"id": existing.id, "updated": True})

    rec = AppDevice(
        user_id=str(current_user.id),
        tenant_id=tenant_id,
        device_token=body.device_token,
        platform=body.platform,
        app_version=body.app_version,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return success_response(data={"id": rec.id, "updated": False}, message="设备已注册")


@router.post("/push/test")
def app_push_test(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """测试 Push 占位（日志模式）。"""
    pending = db.query(Inquiry).filter(Inquiry.status == "pending").count()
    result = notify_inquiry_pending(db, str(current_user.id), max(pending, 1))
    return success_response(data=result, message="推送已发送")


@router.get("/config")
def app_config(current_user: User = Depends(get_current_user)):
    """App 壳配置（Capacitor / PWA）。"""
    import os
    return success_response(
        data={
            "app_name": "出海计",
            "bundle_id": "com.youding.chuhaiji",
            "min_version": "1.0.0",
            "current_version": os.getenv("CHUHAIJI_APP_VERSION", "1.0.0"),
            "tabs": ["assistant", "today", "publish", "profile"],
            "push": {
                "enabled": True,
                "provider": "fcm" if fcm_enabled() else "stub",
                "fcm_configured": fcm_enabled(),
            },
            "store": {
                "capacitor_ready": True,
                "android_package": "com.youding.chuhaiji",
                "ios_bundle": "com.youding.chuhaiji",
                "play_store_url": os.getenv("CHUHAIJI_PLAY_URL", ""),
                "app_store_url": os.getenv("CHUHAIJI_APP_STORE_URL", ""),
            },
            "offline": {"inquiries_cache": True, "max_items": 100},
            "ubrain_path": "/api/v1/ubrain/chat",
        }
    )


@router.get("/store-release")
def app_store_release():
    """APP-1c：商店包版本与更新提示（无需登录）。"""
    import os
    return success_response(
        data={
            "min_version": "1.0.0",
            "latest_version": os.getenv("CHUHAIJI_APP_VERSION", "1.0.0"),
            "force_update": os.getenv("CHUHAIJI_FORCE_UPDATE", "").lower() in ("1", "true"),
            "release_notes": "出海计 v1：四 Tab + Push + 离线询盘缓存",
        }
    )


@router.get("/today")
def app_today_tab(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """今日 Tab：待办 + 蓝海一条。"""
    tenant, err = _tenant(db, current_user)
    if err:
        return err

    pending = count_real_inquiries(db, tenant_id=str(tenant.id), status="pending")
    today = build_today_payload(db=db, tenant=tenant, pending_inquiries=pending)
    path_map = {
        "inquiry": "/client/inquiries",
        "blue_ocean": "/client/assistant",
        "publish": "/client/content",
    }
    todos = []
    for item in today["today_queue"]:
        todos.append(
            {
                "id": item["id"],
                "title": item["label"],
                "path": path_map.get(item["id"], "/client/dashboard"),
                "priority": "high" if item.get("priority") == "high" else "normal",
            }
        )
    hint = today["blue_ocean_hint"]
    return success_response(
        data={
            "todos": todos,
            "today_one_thing": today["today_one_thing"],
            "blue_ocean_hint": {
                "country": hint.get("country_code"),
                "country_label": hint.get("country_label"),
                "reason": hint.get("reason"),
                "category": hint.get("category"),
                "category_key": hint.get("category_key"),
            },
            "disclaimer": hint.get("disclaimer"),
        }
    )


class AppChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


@router.get("/inquiries/offline")
def app_inquiries_offline(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """APP-2：弱网询盘列表缓存包。"""
    tenant, err = _tenant(db, current_user)
    if err:
        return err

    q = db.query(Inquiry).filter(Inquiry.status == "pending")
    if hasattr(Inquiry, "merchant_id"):
        q = q.filter(Inquiry.merchant_id == current_user.id)
    rows = q.order_by(Inquiry.created_at.desc()).limit(min(limit, 100)).all()
    items = []
    for r in rows:
        items.append(
            {
                "id": str(r.id),
                "subject": getattr(r, "subject", None) or getattr(r, "name", "") or "询盘",
                "message": (r.message or "")[:500],
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return success_response(
        data={
            "items": items,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl_seconds": 3600,
        }
    )


class VoiceTranscribeRequest(BaseModel):
    text: str | None = Field(None, max_length=2000)
    note: str | None = Field(None, description="客户端 Web Speech API 转写结果")


@router.post("/voice/transcribe")
def app_voice_transcribe(
    body: VoiceTranscribeRequest,
    current_user: User = Depends(get_current_user),
):
    """APP-2：语音输入占位 — 优先使用客户端 STT 上传的 text。"""
    _ = current_user
    text = (body.text or "").strip()
    if not text:
        return success_response(
            data={
                "text": "",
                "mode": "client_stt_required",
                "hint": "请在 App 内使用浏览器 SpeechRecognition，将结果 POST 到本接口",
            }
        )
    return success_response(data={"text": text, "mode": "client_stt"})


@router.post("/push/publish-failed")
def app_push_publish_failed(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布失败 Push（APP-1b）。"""
    result = notify_publish_failed(db, str(current_user.id), task_id)
    return success_response(data=result)


@router.post("/assistant/chat")
def app_assistant_chat(
    body: AppChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """App 助手 Tab 对话（复用 UBrain）。"""
    tenant, err = _tenant(db, current_user)
    if err:
        return err
    try:
        _task, data = run_chat_task(
            db,
            tenant_id=str(tenant.id),
            message=body.message,
            context={},
            user_id=str(current_user.id),
        )
    except UBrainChatTaskError as exc:
        return error_response(500, str(exc))
    return success_response(data=data)
