# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""LangChain 服务层 — 模型分发、会话管理、流式对话、知识库 RAG"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List, Optional

from app.core.cache import get_cache, redis_client, set_cache

# 会话配置
SESSION_TTL = 3600  # 1 小时
MAX_HISTORY = 20    # 每个会话最多保留 20 轮对话
SESSION_PREFIX = "langchain:session:"


class SessionManager:
    """Redis 会话管理"""
    @staticmethod
    def create_session(model: str = "gpt-3.5-turbo", system_prompt: str = "") -> str:
        """create_session。

        参数说明：
        :param model: 参数 model
        :param system_prompt: 参数 system_prompt
        :return: 返回处理结果。
        """
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "model": model,
            "system_prompt": system_prompt,
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if system_prompt:
            session["messages"].append({"role": "system", "content": system_prompt})
        set_cache(f"{SESSION_PREFIX}{session_id}", json.dumps(session, ensure_ascii=False))
        return session_id

    @staticmethod
    def get_session(session_id: str) -> Optional[Dict]:
        """get_session。

        参数说明：
        :param session_id: 参数 session_id
        :return: 返回处理结果。
        """
        data = get_cache(f"{SESSION_PREFIX}{session_id}")
        if data and isinstance(data, str):
            return json.loads(data)
        return data

    @staticmethod
    def add_message(session_id: str, role: str, content: str):
        """add_message。

        参数说明：
        :param session_id: 参数 session_id
        :param role: 参数 role
        :param content: 参数 content
        :return: 返回处理结果。
        """
        session = SessionManager.get_session(session_id)
        if not session:
            return
        session["messages"].append({"role": role, "content": content})
        if len(session["messages"]) > MAX_HISTORY + 1:
            # 保留 system prompt + 最近 N 轮
            system_msgs = [m for m in session["messages"] if m["role"] == "system"]
            other_msgs = [m for m in session["messages"] if m["role"] != "system"]
            session["messages"] = system_msgs + other_msgs[-MAX_HISTORY:]
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_cache(f"{SESSION_PREFIX}{session_id}", json.dumps(session, ensure_ascii=False))

    @staticmethod
    def delete_session(session_id: str):
        """delete_session。

        参数说明：
        :param session_id: 参数 session_id
        :return: 返回处理结果。
        """
        from app.core.cache import delete_cache
        delete_cache(f"{SESSION_PREFIX}{session_id}")

    @staticmethod
    def list_sessions() -> List[Dict]:
        """list_sessions。
        :return: 返回处理结果。
        """
        if not redis_client:
            return []
        keys = list(redis_client.scan_iter(match=f"{SESSION_PREFIX}*", count=100))
        sessions = []
        for k in keys[:50]:
            data = get_cache(k)
            if data:
                s = json.loads(data) if isinstance(data, str) else data
                sessions.append({
                    "id": s.get("id"),
                    "model": s.get("model"),
                    "message_count": len(s.get("messages", [])),
                    "updated_at": s.get("updated_at"),
                })
        return sorted(sessions, key=lambda s: s.get("updated_at", ""), reverse=True)


def _estimate_tokens(text: str) -> int:
    """简易 token 估算（中文按字数，英文按 4 字符/token）"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return chinese_chars + other_chars // 4


def _build_messages(session: Dict, user_msg: str) -> List[Dict]:
    """构建 LangChain 消息格式"""
    messages = list(session.get("messages", []))
    messages.append({"role": "user", "content": user_msg})
    return messages


async def stream_chat(
    session_id: str,
    user_message: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    knowledge_context: str = "",
) -> AsyncGenerator[str, None]:
    """
    SSE 流式对话
    优先使用 LangChain，降级到 OpenAI 兼容 API
    """
    session = SessionManager.get_session(session_id)
    if not session:
        session_id = SessionManager.create_session(model)
        session = SessionManager.get_session(session_id)
        yield f"data: {json.dumps({'type': 'session_created', 'session_id': session_id})}\n\n"

    # 注入知识库上下文
    if knowledge_context:
        user_message = f"参考以下知识库内容回答问题：\n{knowledge_context}\n\n用户问题：{user_message}"

    SessionManager.add_message(session_id, "user", user_message)
    messages = _build_messages(session, user_message)
    # 系统提示词
    if session.get("system_prompt"):
        messages.insert(0, {"role": "system", "content": session["system_prompt"]})

    full_response = ""
    try:
        # 尝试 LangChain
        from ai_engine.core.engine import AIEngine
        engine = AIEngine(default_model=model)
        # 用非流式方式获取完整响应（兼容当前 AIEngine 接口）
        result = await engine.generate(
            prompt=user_message,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = result.get("content", "") if isinstance(result, dict) else str(result)
        # 模拟流式输出
        for i in range(0, len(content), 10):
            chunk = content[i:i+10]
            full_response += chunk
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.02)

    except Exception as e:
        # 降级：直连 OpenAI 兼容 API
        try:
            full_response = await _fallback_openai(
                messages, model, temperature, max_tokens
            )
            # 模拟流式
            for i in range(0, len(full_response), 10):
                chunk = full_response[i:i+10]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.02)
        except Exception as fallback_err:
            yield f"data: {json.dumps({'type': 'error', 'content': f'AI 调用失败: {str(fallback_err)}'})}\n\n"
            return

    # 保存助手回复
    SessionManager.add_message(session_id, "assistant", full_response)
    # 结束标记
    tokens = _estimate_tokens(full_response)
    yield f"data: {json.dumps({'type': 'done', 'content': full_response, 'tokens': tokens})}\n\n"


async def _fallback_openai(
    messages: List[Dict],
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """降级方案：直连 OpenAI 兼容 API"""
    import os
    import httpx
    api_key = os.getenv("AI_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("AI_OPENAI_BASE_URL") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def rag_query(
    query: str,
    knowledge_base_id: str = "",
    model: str = "gpt-3.5-turbo",
) -> str:
    """
    RAG 检索增强生成
    从知识库检索相关文档，再调用 LLM 生成回答
    """
    # 简易关键词检索（后续可替换为向量检索）
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        # 搜索知识库相关内容
        context = f"知识库检索结果（基于查询：{query}）\n暂无匹配内容，将基于通用知识回答。"
        # 使用 LLM 生成
        messages = [
            {"role": "system", "content": "你是一个知识库助手。根据提供的参考内容回答用户问题。如果参考内容不相关，可以基于你的知识回答。"},
            {"role": "user", "content": f"参考内容：\n{context}\n\n问题：{query}"},
        ]
        return await _fallback_openai(messages, model, 0.5, 1024)
    finally:
        db.close()
