# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""ContentAsset 统一对象 API（修正设计稿 模块4 / 契约 §4）。

端点（完整前缀 = /api + /v1 + ROUTE_PREFIX="/content-assets"）：
- GET  /content-assets                     列表（登录；分页；平台管理员可跨租户）
- GET  /content-assets/{asset_id}          单条（登录；跨租户 403）
- POST /content-assets/{asset_id}/status   状态跃迁（登录 + 租户运营；非法跃迁 409）

约定：
- 一个文件只有一个 `router = APIRouter()`（第二个会静默覆盖第一个）。
- 平台管理员判据复用 SSOT `app.core.tenant_access.is_platform_admin`（不自造第二套）。
- 租户隔离：只能读 `content_masters`（有 tenant_id）；**严禁**触碰 `content_pages` /
  `content_versions`（无 tenant_id，会跨租户泄露）。
- 裁定 裁-3：状态跃迁只接受既有值 `draft` / `ready` / `published`，
  **严禁**写入 `archived` / `verification_failed`（防「漏迁移写新值 → 整条查询 500」）。
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.core.tenant_access import is_platform_admin, is_tenant_operator
from app.db.session import get_db
from app.models.content_master import ContentMaster
from app.models.tenant import UserTenant
from app.models.user import User
from app.schemas.content_asset import ContentAssetListOut, ContentStatusTransitionIn
from app.services.content_asset_service import build_content_asset

ROUTE_PREFIX = "/content-assets"
ROUTE_TAGS = ["内容资产"]

router = APIRouter(tags=["内容资产"])

# 状态跃迁白名单（既有值；裁-3：严禁 archived / verification_failed）
_ALLOWED_STATUSES = frozenset({"draft", "ready", "published"})
# 合法前向跃迁（同一值视为幂等，允许）。published 在本三值集合内为终态。
_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"ready"}),
    "ready": frozenset({"published"}),
    "published": frozenset(),
}
_MAX_PAGE_SIZE = 100


def _coerce_uuid(value: str) -> Optional[str]:
    """校验并规范化 UUID 字符串；非法返回 None（避免非法 UUID 直查 PG → 500）。"""
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError, TypeError):
        return None


def _tenant_link(db: Session, user: User, tenant_id) -> Optional[UserTenant]:
    return (
        db.query(UserTenant)
        .filter(
            UserTenant.tenant_id == str(tenant_id),
            UserTenant.user_id == str(user.id),
            UserTenant.is_active.is_(True),
        )
        .first()
    )


def _is_tenant_member(db: Session, user: User, tenant_id) -> bool:
    """平台管理员放行；否则须为该租户有效成员。"""
    if is_platform_admin(user):
        return True
    return _tenant_link(db, user, tenant_id) is not None


@router.get("")
def list_content_assets(
    tenant_id: Optional[str] = Query(None, description="平台管理员可选的租户过滤"),
    page: int = Query(1, description="页码，>=1"),
    size: int = Query(20, description="每页条数，1..100"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """内容资产列表（分页；租户隔离）。"""
    if page < 1:
        return error_response(400, "page 必须 >= 1")
    if size < 1 or size > _MAX_PAGE_SIZE:
        return error_response(400, f"size 必须在 1..{_MAX_PAGE_SIZE} 之间")

    query = db.query(ContentMaster)
    if is_platform_admin(current_user):
        if tenant_id:
            tid = _coerce_uuid(tenant_id)
            if tid is None:
                return error_response(400, "tenant_id 格式非法")
            query = query.filter(ContentMaster.tenant_id == tid)
    else:
        tenant_ids = [
            row[0]
            for row in db.query(UserTenant.tenant_id)
            .filter(
                UserTenant.user_id == str(current_user.id),
                UserTenant.is_active.is_(True),
            )
            .all()
        ]
        if not tenant_ids:
            empty = ContentAssetListOut(items=[], total=0, page=page, size=size)
            return success_response(data=empty.model_dump(), message="success")
        query = query.filter(ContentMaster.tenant_id.in_(tenant_ids))

    total = query.count()
    rows = (
        query.order_by(ContentMaster.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    items = [build_content_asset(db, m) for m in rows]
    payload = ContentAssetListOut(items=items, total=total, page=page, size=size)
    return success_response(data=payload.model_dump(), message="success")


@router.get("/{asset_id}")
def get_content_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """单条内容资产（跨租户 403）。"""
    aid = _coerce_uuid(asset_id)
    if aid is None:
        return error_response(400, "asset_id 格式非法")
    master = db.query(ContentMaster).filter(ContentMaster.id == aid).first()
    if not master:
        return error_response(404, "内容资产不存在")
    if not _is_tenant_member(db, current_user, master.tenant_id):
        return error_response(403, "无权访问该租户内容资产")
    return success_response(data=build_content_asset(db, master).model_dump(), message="success")


@router.post("/{asset_id}/status")
def transition_content_status(
    asset_id: str,
    req: ContentStatusTransitionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """状态跃迁（只接受 draft/ready/published；非法跃迁 409）。"""
    aid = _coerce_uuid(asset_id)
    if aid is None:
        return error_response(400, "asset_id 格式非法")
    master = db.query(ContentMaster).filter(ContentMaster.id == aid).first()
    if not master:
        return error_response(404, "内容资产不存在")

    # 权限：平台管理员 → 放行；否则须为租户运营（且为有效成员）
    if not is_platform_admin(current_user):
        if not is_tenant_operator(current_user) or _tenant_link(db, current_user, master.tenant_id) is None:
            return error_response(403, "需要租户运营或内容发布权限")

    target = (req.content_status or "").strip().lower()
    if target not in _ALLOWED_STATUSES:
        return error_response(
            400,
            f"content_status 仅支持 {'/'.join(sorted(_ALLOWED_STATUSES))}",
        )
    current = (master.status or "").strip().lower()
    if target != current and target not in _TRANSITIONS.get(current, frozenset()):
        return error_response(409, "illegal_content_status_transition")

    if target != current:
        master.status = target
        db.add(master)
        db.commit()
        db.refresh(master)

    return success_response(data=build_content_asset(db, master).model_dump(), message="已更新")


__all__ = ["router", "ROUTE_PREFIX", "ROUTE_TAGS"]
