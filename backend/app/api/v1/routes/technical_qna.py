# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Technical Q&A 路由 — 基于批准知识库的带引用技术问答（公开端点）。

端点：POST /api/v1/technical-qna
确定性检索，绝不编造技术参数/认证/标准；资料不足时明确返回。
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.db.session import get_db
from app.services.technical_qna_service import build_qa_payload
logger = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/technical-qna"
ROUTE_TAGS = ["技术问答"]

router = APIRouter()


class TechnicalQnaRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500, description="技术问题")
    merchant_id: Optional[str] = Field(None, max_length=36)
    top_k: int = Field(5, ge=1, le=10)


@router.post("", summary="技术问答（基于批准知识库）")
def technical_qna(
    body: TechnicalQnaRequest,
    db: Session = Depends(get_db),
):
    """基于批准知识库回答技术问题，返回引用来源；资料不足时明确提示。"""
    try:
        payload = build_qa_payload(
            db,
            body.question,
            merchant_id=body.merchant_id,
            top_k=body.top_k,
        )
        return success_response(data=payload)
    except Exception as exc:  # noqa: BLE001
        logger = __import__("logging").getLogger(__name__)
        logger.exception("Technical Q&A failed: %s", exc)
        return error_response(500, f"技术问答服务异常：{exc}")
