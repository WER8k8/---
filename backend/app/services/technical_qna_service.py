# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Technical Q&A — 基于批准知识库的带引用技术问答。

确定性检索：仅从 approved (is_active) 知识库返回内容，绝不编造参数/认证/标准。
无匹配时明确返回「资料不足」，不产生幻觉答案。
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.ai_knowledge import AiKnowledgeBase


def _tokenize(text: str) -> set[str]:
    """生成中文二元组 + 拉丁词 token 集合。"""
    tokens: set[str] = set()
    if not text:
        return tokens
    for m in re.findall(r"[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*", str(text)):
        tokens.add(m.lower())
    for run in re.findall(r"[\u4e00-\u9fff]+", str(text)):
        if len(run) == 1:
            tokens.add(run)
        else:
            for i in range(len(run) - 1):
                tokens.add(run[i : i + 2])
    return tokens


def _search_approved_knowledge(
    db: Session,
    question: str,
    top_k: int = 5,
    merchant_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    """在批准（is_active）知识库中做关键词检索，返回带命中的片段。"""
    q = db.query(AiKnowledgeBase).filter(
        AiKnowledgeBase.is_active.is_(True),
        AiKnowledgeBase.content.isnot(None),
    )
    if merchant_id:
        q = q.filter(AiKnowledgeBase.merchant_id == merchant_id)

    q_tokens = _tokenize(question)
    if not q_tokens:
        return []

    scored: list[tuple[float, AiKnowledgeBase]] = []
    for kb in q.all():
        content = kb.content or ""
        kb_tokens = _tokenize(content)
        if not kb_tokens:
            continue
        hit = len(q_tokens & kb_tokens)
        if hit == 0:
            continue
        # 短语整体命中加权
        score = hit / len(q_tokens)
        if question.lower() in content.lower():
            score = max(score, 0.95)
        scored.append((score, kb))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, kb in scored[:top_k]:
        snippet = _extract_snippet(kb.content or "", question)
        results.append({
            "knowledge_id": str(kb.id),
            "title": kb.title,
            "content_type": kb.content_type,
            "snippet": snippet,
            "match_score": round(score * 100, 1),
            "source_file": kb.file_path,
            "updated_at": kb.updated_at.isoformat() if kb.updated_at else None,
        })
    return results


def _extract_snippet(content: str, question: str, width: int = 300) -> str:
    """提取问题附近的内容片段作为引用依据。"""
    low_content = content.lower()
    low_q = question.lower()
    idx = low_content.find(low_q)
    if idx >= 0:
        start = max(0, idx - 80)
        end = min(len(content), idx + width)
        return content[start:end]
    # 无直接命中则取首个非空段落
    for para in content.split("\n"):
        if len(para.strip()) > 20:
            return para.strip()[:width]
    return content[:width]


def answer_technical_question(
    db: Session,
    question: str,
    merchant_id: Optional[str] = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """回答问题：检索批准知识库 → 返回带引用的 grounded 回答。

    无批准资料匹配时，明确返回 insufficient 而非编造答案。
    """
    ts = datetime.now(timezone.utc).isoformat()
    sources = _search_approved_knowledge(db, question, top_k=top_k, merchant_id=merchant_id)
    if not sources:
        return {
            "answer": None,
            "insufficient": True,
            "message": "当前批准知识库中没有足够资料回答该问题，请咨询技术团队或补充相关资料。",
            "sources": [],
            "confidence": 0.0,
            "need_human_review": True,
            "timestamp": ts,
        }

    best = sources[0]
    answer = (
        f"根据批准资料「{best['title']}」：\n\n{best['snippet']}\n\n"
        f"（内容片段，完整资料请查看来源。以上回答基于知识库，未包含未经核实的性能承诺。）"
    )
    return {
        "answer": answer,
        "insufficient": False,
        "message": "回答基于批准知识库，仅供参考。",
        "sources": sources,
        "confidence": best["match_score"] / 100,
        "need_human_review": False,
        "timestamp": ts,
    }


def build_qa_payload(
    db: Session,
    question: str,
    merchant_id: Optional[str] = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """构建 API 响应载荷（含 model/promptVersion/retrievedDocs 记录字段）。"""
    result = answer_technical_question(db, question, merchant_id=merchant_id, top_k=top_k)
    result["model"] = "deterministic-retrieval-v1"
    result["prompt_version"] = "grounded-qna-v1"
    result["retrieved_docs"] = [s["knowledge_id"] for s in result.get("sources", [])]
    result["human_reviewed"] = False
    return result
