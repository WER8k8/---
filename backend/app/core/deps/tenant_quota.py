# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户 Token 配额 — AI 类路由统一扣费入口。"""

from sqlalchemy.orm import Session

from app.services.token_service import InsufficientTokenError, TokenService


def consume_tenant_tokens(
    db: Session,
    tenant_id: str,
    amount: int,
    reason: str,
    reference_id: str | None = None,
) -> int:
    """扣减 Token；余额不足抛出 InsufficientTokenError。"""
    if not tenant_id or amount <= 0:
        return TokenService(db).balance(tenant_id) if tenant_id else 0
    return TokenService(db).consume(tenant_id, amount, reason, reference_id)
