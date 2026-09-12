"""未登录访客视频任务归属：guest_token → tenant_id。"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.media_factory import MediaRenderTask

GUEST_HEADER = "X-Guest-Token"
GUEST_COOKIE = "mf_guest_token"


def new_guest_token() -> str:
    """new_guest_token。
    :return: 返回处理结果。
    """
    return str(uuid.uuid4())


def bind_guest_media_to_tenant(db: Session, guest_token: str, tenant_id: str) -> int:
    """注册成功后，将 guest_token 下未归属任务划到租户。"""
    token = (guest_token or "").strip()
    if not token or not tenant_id:
        return 0
    rows = (
        db.query(MediaRenderTask)
        .filter(
            MediaRenderTask.guest_token == token,
            (MediaRenderTask.tenant_id.is_(None)) | (MediaRenderTask.tenant_id == ""),
        )
        .all()
    )
    for task in rows:
        task.tenant_id = tenant_id
    if rows:
        db.commit()
    return len(rows)


def resolve_guest_token(
    header_value: str | None = None,
    cookie_value: str | None = None,
    body_value: str | None = None,
) -> str | None:
    """resolve_guest_token。

    参数说明：
    :param header_value: 参数 header_value
    :param cookie_value: 参数 cookie_value
    :param body_value: 参数 body_value
    :return: 返回处理结果。
    """
    for raw in (body_value, header_value, cookie_value):
        token = (raw or "").strip()
        if token:
            return token
    return None
