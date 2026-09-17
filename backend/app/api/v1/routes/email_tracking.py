# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""邮件追踪像素路由（P1-3）—— 无需登录鉴权，内置安全防护。"""

import re
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.email_tracking_service import record_open_event, PIXEL_BYTES


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/tracking", tags=["邮件追踪"])

# message_id 格式校验（字母数字下划线横线，1-100 字符）
_MESSAGE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")

# 简易内存限速：每 IP 每分钟 30 次
_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 30
_RATE_WINDOW = 60  # 秒


def _check_rate_limit(ip: str) -> bool:
    """
    处理 _check_rate_limit 相关业务逻辑。

    :param ip: 入参 (str)。

    :return: 返回 bool 类型的结果。
    """
    now = datetime.now(timezone.utc).timestamp()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < _RATE_WINDOW]
    if len(_rate_store[ip]) >= _RATE_LIMIT:
        return False
    _rate_store[ip].append(now)
    return True


@router.get("/pixel/{message_id}.png")
async def tracking_pixel(
    message_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """1x1 追踪像素 —— 每次加载记录打开事件。"""
    # 格式校验
    if not _MESSAGE_ID_RE.match(message_id):
        return Response(content=PIXEL_BYTES, media_type="image/png",
                        headers={"Cache-Control": "no-cache, no-store"})

    # 限速
    ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(ip):
        return Response(content=PIXEL_BYTES, media_type="image/png",
                        headers={"Cache-Control": "no-cache, no-store"})

    # 记录打开事件
    record_open_event(
        db=db,
        message_id=message_id,
        ip_address=ip,
        user_agent=request.headers.get("user-agent", ""),
    )
    db.commit()
    # 返回 1x1 透明 PNG
    return Response(
        content=PIXEL_BYTES,
        media_type="image/png",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
