# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Chat Sessions API Router - AI对话会话API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import get_current_user
from app.models.chat_session import ChatSession
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/chat-sessions"
ROUTE_TAGS = ["AI对话会话"]

router = APIRouter(tags=["chat-sessions"])


@router.post("/", response_model=dict)
def create_chat_session(
    user_id: str,
    session_name: Optional[str] = None,
    model_used: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建AI对话会话"""
    try:
        session = ChatSession(
            user_id=uuid.UUID(user_id),
            session_name=session_name,
            model_used=model_used,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return success_response(data={"id": str(session.id), "session_name": session.session_name, "status": session.status})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}", response_model=dict)
def get_chat_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取对话会话详情"""
    session = db.query(ChatSession).filter(ChatSession.id == uuid.UUID(session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return success_response(data={
        "id": str(session.id),
        "user_id": str(session.user_id),
        "session_name": session.session_name,
        "model_used": session.model_used,
        "total_tokens": session.total_tokens,
        "status": session.status,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    })


@router.get("/by-user/{user_id}", response_model=List[dict])
def list_user_chat_sessions(
    user_id: str,
    status: Optional[str] = None,  # active/archived
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出用户的所有对话会话"""
    query = db.query(ChatSession).filter(ChatSession.user_id == uuid.UUID(user_id))
    if status:
        query = query.filter(ChatSession.status == status)
    
    sessions = query.order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit).all()
    return success_response(data=[
        {
            "id": str(s.id),
            "session_name": s.session_name,
            "model_used": s.model_used,
            "total_tokens": s.total_tokens,
            "status": s.status,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in sessions
    ])


@router.put("/{session_id}", response_model=dict)
def update_chat_session(
    session_id: str,
    session_name: Optional[str] = None,
    model_used: Optional[str] = None,
    status: Optional[str] = None,  # active/archived
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新对话会话"""
    session = db.query(ChatSession).filter(ChatSession.id == uuid.UUID(session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    if session_name is not None:
        session.session_name = session_name
    if model_used is not None:
        session.model_used = model_used
    if status is not None:
        session.status = status
    
    db.commit()
    db.refresh(session)
    return success_response(data={"id": str(session.id), "session_name": session.session_name, "status": session.status})


@router.delete("/{session_id}")
def delete_chat_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除对话会话（软删除，改为archived）"""
    session = db.query(ChatSession).filter(ChatSession.id == uuid.UUID(session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session.status = "archived"
    db.commit()
    return success_response(message="Chat session archived successfully")


@router.post("/{session_id}/add-message", response_model=dict)
def add_message_to_session(
    session_id: str,
    role: str,  # user/assistant/system
    content: str,
    tokens: Optional[int] = None,
    model: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """向会话添加消息"""
    try:
        from app.models.chat_message import ChatMessage
        session = db.query(ChatSession).filter(ChatSession.id == uuid.UUID(session_id)).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        message = ChatMessage(
            session_id=uuid.UUID(session_id),
            role=role,
            content=content,
            tokens=tokens,
            model=model,
        )
        db.add(message)
        # 更新会话的统计信息
        if tokens:
            session.total_tokens += tokens
        session.updated_at = db.func.now()
        db.commit()
        db.refresh(message)
        return success_response(data={
            "id": str(message.id),
            "role": message.role,
            "content": message.content,
            "tokens": message.tokens,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        })
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}/messages", response_model=List[dict])
def get_session_messages(
    session_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话的所有消息"""
    from app.models.chat_message import ChatMessage
    session = db.query(ChatSession).filter(ChatSession.id == uuid.UUID(session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == uuid.UUID(session_id)
    ).order_by(ChatMessage.created_at).offset(skip).limit(limit).all()
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "tokens": m.tokens,
            "model": m.model,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]
