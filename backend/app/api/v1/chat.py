# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional, AsyncGenerator
from app.core.config import settings
from app.core.database import get_db
from app.core.response import success_response
from app.core.no_fake_delivery import mock_allowed, stamp_mock
from app.models.ai_knowledge import AiChatSession, AiChatMessage
import json
import uuid


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/chat"
ROUTE_TAGS = ["AI聊天托管"]

router = APIRouter()

_AI_CHAT_MOCK_FLAG = "AI_CHAT_ALLOW_MOCK"


@router.post("/chat/webhook")
async def ai_chat_webhook(
    merchant_id: str,
    buyer_message: str,
    buyer_country: str = "US",
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
):
    """
    AI时差托管接口 - LangChain + RAG
    接收买家消息，返回AI回复（支持流式）
    """
    secret = (getattr(settings, "AI_CHAT_WEBHOOK_SECRET", None) or "").strip()
    env = (settings.ENVIRONMENT or "").strip().lower()
    if env == "production" and not secret:
        raise HTTPException(status_code=503, detail="AI_CHAT_WEBHOOK_SECRET 未配置")
    if secret and (x_webhook_secret or "").strip() != secret:
        raise HTTPException(status_code=403, detail="webhook 密钥无效")
    # 1. 查找或创建会话
    if session_id:
        session = db.query(AiChatSession).filter(
            AiChatSession.id == session_id,
            AiChatSession.merchant_id == merchant_id
        ).first()
    else:
        session = None

    if not session:
        session = AiChatSession(
            id=str(uuid.uuid4()),
            merchant_id=merchant_id,
            buyer_country=buyer_country,
            buyer_language=_detect_language(buyer_country),
            session_status="active",
            ai_mode=True
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # 2. 保存买家消息
    user_msg = AiChatMessage(
        id=str(uuid.uuid4()),
        session_id=session.id,
        role="user",
        content=buyer_message,
        language=session.buyer_language or "en"
    )
    db.add(user_msg)
    # 3. 更新会话消息计数
    session.message_count = (session.message_count or 0) + 1
    db.commit()
    # 4. 真实 LLM/RAG 未接入时：生产禁止假回复；开发须显式 mock 标记
    if not _ai_chat_backend_ready():
        if not mock_allowed(_AI_CHAT_MOCK_FLAG):
            raise HTTPException(
                status_code=503,
                detail={
                    "error_code": "AI_REPLY_NOT_CONFIGURED",
                    "message": "AI 接待未配置，禁止返回模拟话术冒充真实回复",
                },
            )
        ai_reply = _dev_mock_reply(buyer_country, session.message_count or 0)
        mock_mode = True
    else:
        ai_reply = _invoke_ai_rag_reply(buyer_message, buyer_country, session.message_count or 0)
        mock_mode = False

    # 5. 保存AI回复
    assistant_msg = AiChatMessage(
        id=str(uuid.uuid4()),
        session_id=session.id,
        role="assistant",
        content=ai_reply,
        language=session.buyer_language or "en"
    )
    db.add(assistant_msg)
    db.commit()
    payload = {
        "session_id": str(session.id),
        "reply": ai_reply,
        "message_count": session.message_count,
        "should_ask_email": session.message_count >= 3,  # KPI: 第3句开始索要邮箱
    }
    if mock_mode:
        return stamp_mock(payload, reason="ai_chat_llm_not_configured")
    return success_response(data=payload)


def _ai_chat_backend_ready() -> bool:
    """真实接待：须配置可调用 LLM（禁止无配置仍 200）。"""
    return bool(
        (settings.AI_OPENAI_API_KEY or settings.AI_ANTHROPIC_API_KEY or "").strip()
    )


def _detect_language(country_code: str) -> str:
    """根据国家代码检测语言"""
    lang_map = {
        "CN": "zh", "SA": "ar", "AE": "ar", "BR": "pt", "RU": "ru",
        "DE": "de", "FR": "fr", "ES": "es", "US": "en", "TH": "th",
        "VN": "vi", "JP": "ja", "KR": "ko", "NG": "en", "KE": "en"
    }
    return lang_map.get(country_code, "en")


def _dev_mock_reply(country: str, msg_count: int) -> str:
    """仅 development / AI_CHAT_ALLOW_MOCK=1；响应带 mode=mock。"""
    if msg_count >= 3:
        return (
            "[DEV-MOCK] Thank you for your inquiry! Please leave your email for a formal quotation."
        )
    return (
        "[DEV-MOCK] Hello! Please share mesh weight (g/m²), mesh size (mm), and destination port."
    )


def _invoke_ai_rag_reply(message: str, country: str, msg_count: int) -> str:
    """生产路径：RAG 引擎接入点；未实现必须失败，禁止模板冒充。"""
    raise HTTPException(
        status_code=501,
        detail={
            "error_code": "AI_REPLY_ENGINE_NOT_IMPLEMENTED",
            "message": "已配置 API Key 但 RAG 引擎未实现，禁止硬编码冒充",
        },
    )


@router.get("/chat/sessions/{session_id}")
async def get_chat_session(session_id: str, db: Session = Depends(get_db)):
    """获取聊天会话历史"""
    session = db.query(AiChatSession).filter(AiChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = db.query(AiChatMessage).filter(
        AiChatMessage.session_id == session_id
    ).order_by(AiChatMessage.created_at.asc()).all()
    return success_response(data={
        "session_id": str(session.id),
        "buyer_country": session.buyer_country,
        "buyer_email": session.buyer_email,
        "message_count": session.message_count,
        "session_status": session.session_status,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None
            } for m in messages
        ]
    })


@router.post("/chat/sessions/{session_id}/email")
async def update_session_email(session_id: str, email: str, phone: Optional[str] = None, db: Session = Depends(get_db)):
    """更新会话邮箱（KPI达成）"""
    session = db.query(AiChatSession).filter(AiChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    session.buyer_email = email
    session.buyer_phone = phone
    session.session_status = "converted"  # 标记为已转化
    db.commit()
    return success_response(message="邮箱已记录，技术经理将在2小时内回复正式报价单")
