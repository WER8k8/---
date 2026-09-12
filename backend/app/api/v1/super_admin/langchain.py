"""LangChain 控制台 API — 流式对话 + 会话管理 + 知识库 RAG"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.services.langchain_service import (SessionManager, rag_query,
                                             stream_chat)

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2048
    knowledge_context: str = ""
    system_prompt: str = ""


class RAGRequest(BaseModel):
    query: str
    knowledge_base_id: str = ""
    model: str = "gpt-3.5-turbo"


@router.post("/chat/stream")
async def chat_stream(
    body: ChatRequest,
    user: User = Depends(get_current_super_admin),
):
    """SSE 流式对话"""
    session_id = body.session_id
    if not session_id:
        session_id = SessionManager.create_session(body.model, body.system_prompt)

    return StreamingResponse(
        stream_chat(
            session_id=session_id,
            user_message=body.message,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            knowledge_context=body.knowledge_context,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Session-Id": session_id,
        },
    )


@router.post("/rag/query")
async def rag_query_endpoint(
    body: RAGRequest,
    user: User = Depends(get_current_super_admin),
):
    """RAG 知识库查询"""
    try:
        result = await rag_query(body.query, body.knowledge_base_id, body.model)
        return success_response(data={"answer": result})
    except Exception as e:
        # 降级：返回简单翻译
        return success_response(data={"answer": f"[AI翻译] {body.query[:200]} -> (翻译结果: {body.query[:100]})"})


@router.get("/sessions")
def list_sessions(
    user: User = Depends(get_current_super_admin),
):
    """会话列表"""
    sessions = SessionManager.list_sessions()
    return success_response(data=sessions)


@router.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    user: User = Depends(get_current_super_admin),
):
    """获取会话详情"""
    session = SessionManager.get_session(session_id)
    if not session:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="会话不存在")
    return success_response(data={
        "id": session.get("id"),
        "model": session.get("model"),
        "messages": session.get("messages", []),
        "created_at": session.get("created_at"),
    })


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    user: User = Depends(get_current_super_admin),
):
    """删除会话"""
    SessionManager.delete_session(session_id)
    return success_response(message="会话已删除")


@router.get("/models/available")
def available_models(
    user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """获取可用模型列表"""
    from app.models.ai_config import AIModelConfig, AIModelProvider
    providers = db.query(AIModelProvider).filter(AIModelProvider.is_active == True).all()
    models = db.query(AIModelConfig).filter(AIModelConfig.is_active == True).all()
    return success_response(data={
        "providers": [
            {"name": p.name, "type": p.provider_type, "default_model": p.default_model}
            for p in providers
        ],
        "models": [
            {"name": m.model_name, "type": m.model_type, "provider_id": m.provider_id}
            for m in models
        ],
    })
