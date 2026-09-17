# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""WhatsApp Business Cloud API 路由 — FIX-54"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.security import get_current_user
from app.services.ubrain.whatsapp_business_service import (
    WhatsAppBusinessClient,
    WhatsAppLanguage,
    WhatsAppTemplateCategory,
    whatsapp_business_client,
    whatsapp_outreach_service,
)

ROUTE_PREFIX = ""
router = APIRouter(prefix="/whatsapp", tags=["获客·WhatsApp"])


# ── 消息发送 ──────────────────────────────────────────────

@router.post("/send/text")
async def send_text(
    to: str,
    body: str,
    preview_url: bool = True,
    user=Depends(get_current_user),
):
    """发送文本消息"""
    if not whatsapp_business_client.is_configured:
        raise HTTPException(status_code=400, detail="WhatsApp 未配置（WHATSAPP_PHONE_NUMBER_ID + WHATSAPP_ACCESS_TOKEN）")

    result = await whatsapp_business_client.send_text(to=to, body=body, preview_url=preview_url)
    return {"code": 0, "data": result.to_dict()}


@router.post("/send/template")
async def send_template(
    to: str,
    template_name: str,
    language: str = "en",
    components: Optional[list[dict]] = None,
    user=Depends(get_current_user),
):
    """发送模板消息"""
    if not whatsapp_business_client.is_configured:
        raise HTTPException(status_code=400, detail="WhatsApp 未配置")

    try:
        lang = WhatsAppLanguage(language)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的语言: {language}")

    result = await whatsapp_business_client.send_template(
        to=to,
        template_name=template_name,
        language=lang,
        components=components,
    )
    return {"code": 0, "data": result.to_dict()}


@router.post("/send/image")
async def send_image(
    to: str,
    image_url: str = "",
    image_id: str = "",
    caption: str = "",
    user=Depends(get_current_user),
):
    """发送图片"""
    if not whatsapp_business_client.is_configured:
        raise HTTPException(status_code=400, detail="WhatsApp 未配置")

    result = await whatsapp_business_client.send_image(
        to=to, image_url=image_url, image_id=image_id, caption=caption,
    )
    return {"code": 0, "data": result.to_dict()}


@router.post("/send/document")
async def send_document(
    to: str,
    document_url: str = "",
    document_id: str = "",
    filename: str = "",
    caption: str = "",
    user=Depends(get_current_user),
):
    """发送文档"""
    if not whatsapp_business_client.is_configured:
        raise HTTPException(status_code=400, detail="WhatsApp 未配置")

    result = await whatsapp_business_client.send_document(
        to=to, document_url=document_url, document_id=document_id,
        filename=filename, caption=caption,
    )
    return {"code": 0, "data": result.to_dict()}


@router.post("/send/interactive")
async def send_interactive(
    to: str,
    body_text: str,
    buttons: list[dict],
    header_text: str = "",
    footer_text: str = "",
    user=Depends(get_current_user),
):
    """发送交互式消息（按钮）"""
    if not whatsapp_business_client.is_configured:
        raise HTTPException(status_code=400, detail="WhatsApp 未配置")

    result = await whatsapp_business_client.send_interactive(
        to=to, body_text=body_text, buttons=buttons,
        header_text=header_text, footer_text=footer_text,
    )
    return {"code": 0, "data": result.to_dict()}


# ── 模板管理 ──────────────────────────────────────────────

@router.post("/templates")
async def create_template(
    name: str,
    category: str,
    language: str = "en",
    components: Optional[list[dict]] = None,
    user=Depends(get_current_user),
):
    """创建消息模板"""
    if not whatsapp_business_client.is_configured:
        raise HTTPException(status_code=400, detail="WhatsApp 未配置")

    try:
        cat = WhatsAppTemplateCategory(category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的类别: {category}")

    try:
        lang = WhatsAppLanguage(language)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的语言: {language}")

    result = await whatsapp_business_client.create_template(
        name=name, category=cat, language=lang, components=components,
    )
    return {"code": 0, "data": result.to_dict()}


@router.get("/templates")
async def list_templates(
    limit: int = 50,
    status: str = "",
    language: str = "",
    user=Depends(get_current_user),
):
    """查询模板列表"""
    if not whatsapp_business_client.is_configured:
        raise HTTPException(status_code=400, detail="WhatsApp 未配置")

    templates = await whatsapp_business_client.list_templates(
        limit=limit, status=status, language=language,
    )
    return {"code": 0, "data": [t.to_dict() for t in templates]}


@router.delete("/templates/{template_name}")
async def delete_template(
    template_name: str,
    user=Depends(get_current_user),
):
    """删除模板"""
    if not whatsapp_business_client.is_configured:
        raise HTTPException(status_code=400, detail="WhatsApp 未配置")

    try:
        ok = await whatsapp_business_client.delete_template(template_name)
        return {"code": 0, "data": {"deleted": ok}}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── 媒体管理 ──────────────────────────────────────────────

@router.get("/media/{media_id}")
async def get_media_url(
    media_id: str,
    user=Depends(get_current_user),
):
    """获取媒体下载 URL"""
    if not whatsapp_business_client.is_configured:
        raise HTTPException(status_code=400, detail="WhatsApp 未配置")

    url = await whatsapp_business_client.get_media_url(media_id)
    return {"code": 0, "data": {"url": url}}


# ── 商业资料 ──────────────────────────────────────────────

@router.get("/profile")
async def get_business_profile(user=Depends(get_current_user)):
    """获取商业资料"""
    if not whatsapp_business_client.is_configured:
        raise HTTPException(status_code=400, detail="WhatsApp 未配置")

    profile = await whatsapp_business_client.get_business_profile()
    return {"code": 0, "data": profile}


@router.put("/profile")
async def update_business_profile(
    about: str = "",
    address: str = "",
    description: str = "",
    email: str = "",
    websites: Optional[list[str]] = None,
    vertical: str = "",
    user=Depends(get_current_user),
):
    """更新商业资料"""
    if not whatsapp_business_client.is_configured:
        raise HTTPException(status_code=400, detail="WhatsApp 未配置")

    ok = await whatsapp_business_client.update_business_profile(
        about=about, address=address, description=description,
        email=email, websites=websites, vertical=vertical,
    )
    return {"code": 0, "data": {"updated": ok}}


# ── 获客外联 ──────────────────────────────────────────────

@router.post("/outreach/intro")
async def send_outreach_intro(
    to_phone: str,
    prospect_name: str,
    sender_name: str,
    company_name: str,
    industry: str,
    value_prop: str,
    user=Depends(get_current_user),
):
    """发送获客开场白"""
    if not whatsapp_outreach_service.is_configured:
        raise HTTPException(status_code=400, detail="WhatsApp 未配置")

    result = await whatsapp_outreach_service.send_prospect_intro(
        to_phone=to_phone,
        prospect_name=prospect_name,
        sender_name=sender_name,
        company_name=company_name,
        industry=industry,
        value_prop=value_prop,
    )
    return {"code": 0, "data": result.to_dict()}


@router.post("/outreach/follow-up")
async def send_outreach_follow_up(
    to_phone: str,
    prospect_name: str,
    topic: str,
    reference_company: str,
    result: str,
    user=Depends(get_current_user),
):
    """发送获客跟进"""
    result = await whatsapp_outreach_service.send_prospect_follow_up(
        to_phone=to_phone,
        prospect_name=prospect_name,
        topic=topic,
        reference_company=reference_company,
        result=result,
    )
    return {"code": 0, "data": result.to_dict()}


@router.post("/outreach/case-study")
async def send_case_study(
    to_phone: str,
    prospect_name: str,
    stat_percent: str,
    industry: str,
    solution: str,
    benefit: str,
    case_company: str,
    case_result: str,
    case_url: str,
    user=Depends(get_current_user),
):
    """发送案例研究"""
    result = await whatsapp_outreach_service.send_case_study(
        to_phone=to_phone,
        prospect_name=prospect_name,
        stat_percent=stat_percent,
        industry=industry,
        solution=solution,
        benefit=benefit,
        case_company=case_company,
        case_result=case_result,
        case_url=case_url,
    )
    return {"code": 0, "data": result.to_dict()}


# ── Webhook ───────────────────────────────────────────────

@router.get("/webhook")
async def whatsapp_webhook_verify(
    request: Request,
    hub_mode: str = Query("", alias="hub.mode"),
    hub_verify_token: str = Query("", alias="hub.verify_token"),
    hub_challenge: str = Query("", alias="hub.challenge"),
):
    """Webhook 验证（GET 请求）"""
    from app.services.ubrain.whatsapp_business_service import WhatsAppBusinessClient
    ok, challenge = WhatsAppBusinessClient.verify_webhook(
        mode=hub_mode,
        token=hub_verify_token,
        challenge=hub_challenge,
    )
    if ok:
        return int(challenge)
    raise HTTPException(status_code=403, detail="验证失败")


@router.post("/webhook")
async def whatsapp_webhook_event(
    request: Request,
    user=Depends(get_current_user),
):
    """Webhook 事件接收（POST 请求）"""
    from app.services.ubrain.whatsapp_business_service import WhatsAppBusinessClient
    payload = await request.json()
    x_hub_signature = request.headers.get("X-Hub-Signature-256", "")
    ok, messages = WhatsAppBusinessClient.parse_incoming_message(
        payload, signature=x_hub_signature,
    )
    statuses = WhatsAppBusinessClient.parse_status_update(payload)
    return {
        "code": 0,
        "data": {
            "signature_verified": ok,
            "messages": [m.to_dict() for m in messages],
            "status_updates": statuses,
        },
    }


@router.get("/status")
async def whatsapp_status(user=Depends(get_current_user)):
    """WhatsApp 配置状态"""
    return {
        "code": 0,
        "data": {
            "configured": whatsapp_business_client.is_configured,
            "phone_number_id": bool(whatsapp_business_client._phone_number_id),
            "access_token": bool(whatsapp_business_client._access_token),
            "waba_id": bool(whatsapp_business_client._waba_id),
        },
    }
