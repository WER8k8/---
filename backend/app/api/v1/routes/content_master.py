"""统一发布母版 API"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.core.tenant_access import is_platform_admin, user_has_module_permission
from app.db.session import get_db
from app.models.content import Platform, PlatformAccount, PublishTask
from app.models.content_master import ContentMaster
from app.models.tenant import Tenant, UserTenant
from app.models.user import User
from app.services.hub_urls import build_dual_links
from app.services.foreign_trade.publish_preflight_checklist_service import (
    apply_preflight_checklist,
    load_preflight_checklist,
    validate_preflight,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/content-masters", tags=["统一发布母版"])


class ContentMasterCreate(BaseModel):
    tenant_id: str
    title: str = Field(..., min_length=1, max_length=500)
    body: Optional[str] = None
    media_urls: list[str] = Field(default_factory=list)
    content_type: str = "article"
    tenant_canonical_url: Optional[str] = None
    hub_summary: Optional[str] = None
    show_on_hub: bool = True


class ContentMasterUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    media_urls: Optional[list[str]] = None
    status: Optional[str] = None
    tenant_canonical_url: Optional[str] = None
    hub_summary: Optional[str] = None
    show_on_hub: Optional[bool] = None
    preflight_checklist: Optional[dict[str, bool]] = None


class PublishFromMasterRequest(BaseModel):
    platform_ids: list[str] = Field(..., min_length=1)
    account_ids: Optional[list[str]] = None
    primary_url: Optional[str] = None
    secondary_url: Optional[str] = None
    preflight_checklist: Optional[dict[str, bool]] = None
    preflight_force: bool = False


class PublishAutoVariantsRequest(BaseModel):
    platform_ids: list[str] = Field(..., min_length=1)
    draft_ids: Optional[list[str]] = Field(
        None,
        description="GEO 内容矩阵任务返回的 masters.id 列表；为空则用最近草稿",
    )
    fallback_master_id: Optional[str] = None
    primary_url: Optional[str] = None
    secondary_url: Optional[str] = None
    preflight_checklist: Optional[dict[str, bool]] = None
    preflight_force: bool = False


def _tenant_access(user: User, tenant_id: str, db: Session) -> bool:
    """
    处理 _tenant_access 相关业务逻辑。

    :param user: 入参 (User)。
    :param tenant_id: 入参 (str)。
    :param db: 入参 (Session)。

    :return: 返回 bool 类型的结果。
    """
    if is_platform_admin(user):
        return True
    if not user_has_module_permission(user, "content", "read"):
        return False
    link = (
        db.query(UserTenant)
        .filter(
            UserTenant.user_id == user.id,
            UserTenant.tenant_id == tenant_id,
            UserTenant.is_active,
        )
        .first()
    )
    return link is not None


def _guard_publish_preflight(
    master: ContentMaster,
    checklist: dict[str, bool] | None,
    *,
    force: bool = False,
):
    """
    处理 _guard_publish_preflight 相关业务逻辑。

    :param master: 入参 (ContentMaster)。
    :param checklist: 入参 (dict[str, bool] | None)。
    :param force: 入参 (bool)。

    :return: 返回处理结果（或 None）。
    """
    pf = validate_preflight(master, checklist or {}, force=force)
    if pf.get("blocked"):
        from app.core.response import APIResponse
        return APIResponse(code=400, message=str(pf.get("message") or "preflight_blocked"), data=pf)
    return None


def _resolve_preflight_checklist(
    master: ContentMaster,
    checklist: dict[str, bool] | None,
) -> dict[str, bool]:
    """
    处理 _resolve_preflight_checklist 相关业务逻辑。

    :param master: 入参 (ContentMaster)。
    :param checklist: 入参 (dict[str, bool] | None)。

    :return: 返回 dict[str, bool] 类型的结果。
    """
    if checklist is not None:
        return checklist
    return load_preflight_checklist(master)


def _serialize(row: ContentMaster) -> dict[str, Any]:
    """
    处理 _serialize 相关业务逻辑。

    :param row: 入参 (ContentMaster)。

    :return: 返回 dict[str, Any] 类型的结果。
    """
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "title": row.title,
        "body": row.body,
        "media_urls": row.media_urls or [],
        "content_type": row.content_type,
        "tenant_canonical_url": row.tenant_canonical_url,
        "status": row.status,
        "hub_slug": row.hub_slug,
        "hub_summary": row.hub_summary,
        "show_on_hub": row.show_on_hub,
        "preflight_checklist": load_preflight_checklist(row),
        "preflight_approved_at": row.preflight_approved_at.isoformat()
        if row.preflight_approved_at
        else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("")
def list_content_masters(
    tenant_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出（list_content_masters）：处理相关业务逻辑并返回结果。

    :param tenant_id: 入参 (Optional[str])。
    :param page: 入参 (int)。
    :param page_size: 入参 (int)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    q = db.query(ContentMaster)
    if tenant_id:
        if not _tenant_access(current_user, tenant_id, db):
            return error_response(403, "无权访问该租户")
        q = q.filter(ContentMaster.tenant_id == tenant_id)
    elif not is_platform_admin(current_user):
        if not user_has_module_permission(current_user, "content", "read"):
            return error_response(403, "缺少权限: content:read")
        tenant_ids = [
            ut.tenant_id
            for ut in db.query(UserTenant)
            .filter(UserTenant.user_id == current_user.id, UserTenant.is_active)
            .all()
        ]
        if not tenant_ids:
            return success_response(data={"items": [], "total": 0, "page": page, "page_size": page_size})
        q = q.filter(ContentMaster.tenant_id.in_(tenant_ids))
    total = q.count()
    items = (
        q.order_by(ContentMaster.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success_response(
        data={
            "items": [_serialize(i) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.post("")
def create_content_master(
    req: ContentMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建（create_content_master）：处理相关业务逻辑并返回结果。

    :param req: 入参 (ContentMasterCreate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if not _tenant_access(current_user, req.tenant_id, db):
        return error_response(403, "无权操作该租户")
    row = ContentMaster(
        tenant_id=req.tenant_id,
        title=req.title,
        body=req.body,
        media_urls=req.media_urls,
        content_type=req.content_type,
        tenant_canonical_url=req.tenant_canonical_url,
        hub_summary=req.hub_summary,
        show_on_hub=req.show_on_hub,
        created_by=current_user.id,
        status="draft",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return success_response(data=_serialize(row), message="母版已创建")


@router.post("/publish-auto-variants")
def publish_auto_variants_route(
    req: PublishAutoVariantsRequest,
    tenant_id: Optional[str] = Query(None, description="超管可指定租户"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按平台名匹配 [平台] 变体草稿，创建多平台发布任务（人审后调用）。"""
    effective_tenant = tenant_id
    if not effective_tenant:
        link = (
            db.query(UserTenant)
            .filter(
                UserTenant.user_id == current_user.id,
                UserTenant.is_active.is_(True),
            )
            .first()
        )
        if link:
            effective_tenant = str(link.tenant_id)
    if not effective_tenant:
        return error_response(400, "未绑定租户")
    if tenant_id and not _tenant_access(current_user, tenant_id, db):
        return error_response(403, "无权操作该租户")
    fallback = None
    if req.fallback_master_id:
        fallback = db.query(ContentMaster).filter(ContentMaster.id == req.fallback_master_id).first()
    elif req.draft_ids:
        fallback = db.query(ContentMaster).filter(ContentMaster.id == req.draft_ids[0]).first()
    if fallback:
        checklist = _resolve_preflight_checklist(fallback, req.preflight_checklist)
        blocked = _guard_publish_preflight(fallback, checklist, force=req.preflight_force)
        if blocked:
            return blocked
        apply_preflight_checklist(
            fallback,
            checklist,
            user_id=str(current_user.id),
        )
        db.commit()
    from app.services.content_master_publish_service import publish_auto_variants
    try:
        data = publish_auto_variants(
            db,
            tenant_id=str(effective_tenant),
            platform_ids=req.platform_ids,
            draft_ids=req.draft_ids,
            fallback_master_id=req.fallback_master_id,
            primary_url=req.primary_url,
            secondary_url=req.secondary_url,
        )
    except ValueError as exc:
        code = str(exc)
        messages = {
            "tenant_not_found": "租户不存在",
            "no_drafts": "没有可用草稿，请先运行 GEO 内容矩阵",
            "no_platforms": "未找到有效平台",
            "no_tasks_created": "无可用平台账号，请先配置 platform_accounts",
        }
        return error_response(400, messages.get(code, code))
    return success_response(
        data=data,
        message=f"已创建 {data['count']} 条发布任务（按平台变体匹配）",
    )


@router.get("/{master_id}")
def get_content_master(
    master_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_content_master）：处理相关业务逻辑并返回结果。

    :param master_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    row = db.query(ContentMaster).filter(ContentMaster.id == master_id).first()
    if not row:
        return error_response(404, "母版不存在")
    if not _tenant_access(current_user, row.tenant_id, db):
        return error_response(403, "无权访问")
    return success_response(data=_serialize(row))


@router.get("/{master_id}/link-preview")
def preview_publish_links(
    master_id: str,
    platform_code: str = Query("pilot", max_length=64),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布文案双链预览（主链租户域 + 次链枢纽页）。"""
    row = db.query(ContentMaster).filter(ContentMaster.id == master_id).first()
    if not row:
        return error_response(404, "母版不存在")
    if not _tenant_access(current_user, row.tenant_id, db):
        return error_response(403, "无权访问")
    # 复用已加载的 row 中的 tenant_id，避免额外查询（如需要可缓存）
    tenant = db.query(Tenant).filter(Tenant.id == row.tenant_id).first()
    if not tenant:
        return error_response(400, "租户不存在")
    primary, secondary = build_dual_links(tenant, row, platform_code)
    return success_response(
        data={
            "primary_url": primary,
            "secondary_url": secondary,
            "show_on_hub": row.show_on_hub,
            "platform_code": platform_code,
        }
    )


@router.put("/{master_id}")
def update_content_master(
    master_id: str,
    req: ContentMasterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新（update_content_master）：处理相关业务逻辑并返回结果。

    :param master_id: 入参 (str)。
    :param req: 入参 (ContentMasterUpdate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    row = db.query(ContentMaster).options(joinedload(ContentMaster.platforms)).filter(ContentMaster.id == master_id).first()
    if not row:
        return error_response(404, "母版不存在")
    if not _tenant_access(current_user, row.tenant_id, db):
        return error_response(403, "无权操作")
    data = req.model_dump(exclude_unset=True)
    checklist = data.pop("preflight_checklist", None)
    for k, v in data.items():
        setattr(row, k, v)
    if checklist is not None:
        apply_preflight_checklist(row, checklist, user_id=str(current_user.id))
    db.commit()
    db.refresh(row)
    return success_response(data=_serialize(row), message="已更新")


@router.post("/{master_id}/publish")
def publish_from_master(
    master_id: str,
    req: PublishFromMasterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从母版创建多平台发布任务。"""
    # 优化：使用 joinedload 预加载关联数据
    row = db.query(ContentMaster).options(joinedload(ContentMaster.platforms)).filter(ContentMaster.id == master_id).first()
    if not row:
        return error_response(404, "母版不存在")
    if not _tenant_access(current_user, row.tenant_id, db):
        return error_response(403, "无权操作")
    checklist = _resolve_preflight_checklist(row, req.preflight_checklist)
    blocked = _guard_publish_preflight(row, checklist, force=req.preflight_force)
    if blocked:
        return blocked
    apply_preflight_checklist(row, checklist, user_id=str(current_user.id))
    platforms = (
        db.query(Platform)
        .filter(Platform.id.in_(req.platform_ids), Platform.is_active)
        .all()
    )
    if not platforms:
        return error_response(400, "未找到有效平台")
    # 优化：使用 selectinload 预加载租户信息
    from sqlalchemy.orm import selectinload
    tenant = (
        db.query(Tenant)
        .options(selectinload(Tenant.plan))
        .filter(Tenant.id == row.tenant_id)
        .first()
    )
    if not tenant:
        return error_response(400, "租户不存在")
    task_ids: list[str] = []
    for plat in platforms:
        account = None
        if req.account_ids:
            account = (
                db.query(PlatformAccount)
                .filter(
                    PlatformAccount.id.in_(req.account_ids),
                    PlatformAccount.platform_id == plat.id,
                    PlatformAccount.is_active,
                )
                .first()
            )
        if not account:
            account = (
                db.query(PlatformAccount)
                .filter(
                    PlatformAccount.platform_id == plat.id,
                    PlatformAccount.is_active,
                )
                .first()
            )
        if not account:
            continue
        plat_code = (plat.name or "platform")[:32].replace(" ", "_")
        auto_primary, auto_secondary = build_dual_links(tenant, row, plat_code)
        primary = req.primary_url or auto_primary
        secondary = req.secondary_url if req.secondary_url is not None else auto_secondary
        task = PublishTask(
            content_master_id=row.id,
            content_id=None,
            platform_id=plat.id,
            account_id=account.id,
            region=getattr(plat, "region", None) or "cn",
            primary_url=primary,
            secondary_url=secondary,
            status="pending",
        )
        db.add(task)
        db.flush()
        task_ids.append(task.id)
    if not task_ids:
        return error_response(400, "无可用平台账号，请先配置 platform_accounts")
    row.status = "ready"
    db.commit()
    return success_response(
        data={"task_ids": task_ids, "count": len(task_ids)},
        message=f"已创建 {len(task_ids)} 条发布任务",
    )


@router.delete("/{master_id}")
def delete_content_master(
    master_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除（delete_content_master）：处理相关业务逻辑并返回结果。

    :param master_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    row = db.query(ContentMaster).filter(ContentMaster.id == master_id).first()
    if not row:
        return error_response(404, "母版不存在")
    if not _tenant_access(current_user, row.tenant_id, db):
        return error_response(403, "无权操作")
    db.delete(row)
    db.commit()
    return success_response(message="已删除")
