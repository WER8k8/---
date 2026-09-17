# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一视频发布 API — Hermes 编排，一个入口，真发到各视频平台。"""



from app.services.hermes.companion_launch import (
    CompanionLaunchError,
    build_article_companion_payload,
    build_video_companion_payload,
    companion_launch_meta,
)
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session



from app.core.response import error_response, success_response

from app.core.security import get_current_user

from app.db.session import get_db

from app.models.user import User

from app.services.publish_capability_registry import publish_stack_summary, video_publish_capability

from app.services.publish_dispatch_service import publisher_key_for_platform

from app.services.publish_workers.tier_router import preflight_workers
from app.services.hermes.browser_companion import browser_companion_hint, list_browser_companions

from app.services.tenant_scenario_service import resolve_tenant_id_for_user

from app.services.tenant_aitoearn_slot_service import assign_aitoearn_accounts_to_tenant
from app.services.video_bind_hub_service import build_video_bind_hub, sync_aitoearn_accounts_to_tenant
from app.services.publish_workers.sau_worker import sau_check_tenant_platforms
from app.core.tenant_access import (
    deny_unless_module,
    deny_unless_platform_admin,
    is_tenant_staff,
)


def _video_read_guard(user: User):
    """执行 video_read_guard 相关逻辑处理。
    
    :param user: 用户对象
    :return: 返回处理结果。
    """
    if is_tenant_staff(user):
        return None
    return error_response(403, "无权查看")


def _video_publish_guard(user: User):
    """执行 video_publish_guard 相关逻辑处理。
    
    :param user: 用户对象
    :return: 返回处理结果。
    """
    return deny_unless_module(user, "content", "publish")


class AitoearnAssignBody(BaseModel):
    tenant_id: str = Field(..., description="租户 UUID")
    account_ids: list[str] = Field(..., min_length=1, description="AiToEarn 创作者 accountId 列表（一个登录下的整组）")
    bundle_id: str | None = Field(default=None, description="可选 bundle 标识")
    label: str | None = Field(default=None, description="运维备注")




# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/publish", tags=["视频发布"])





class VideoDistributeBody(BaseModel):

    media_task_id: str = Field(..., description="多媒体工厂渲染任务 ID")
    platform_ids: list[str] = Field(default_factory=list, description="目标平台 UUID 列表")
    include_tenant_site: bool = Field(default=True, description="是否同步登记租户官网视频页")
    scheduled_at: datetime | None = Field(
        default=None,
        description="定时发布时间（UTC）；经 AiToEarn publishTime 下发，未到时间返回 pending",
    )





class VideoMatrixHermesBody(BaseModel):

    media_task_id: str = Field(..., description="多媒体工厂渲染任务 ID")
    platform_ids: list[str] = Field(default_factory=list)
    include_tenant_site: bool = Field(default=True)
    message: str = Field(default="视频矩阵真发", max_length=500)
    scheduled_at: datetime | None = Field(
        default=None,
        description="定时发布时间（UTC）；经 AiToEarn publishTime 下发",
    )





@router.get("/video/bind-hub")
async def video_publish_bind_hub(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """一次登录 · 视频发布绑号入口（优丁账号 + AiToEarn 同步状态）。"""
    denied = _video_read_guard(current_user)
    if denied:
        return denied
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    data = await build_video_bind_hub(db, tenant_id=str(tenant_id) if tenant_id else None)
    return success_response(data=data)


@router.get("/video/sau-check")
async def video_sau_account_check(
    platform_name: str | None = Query(None, description="可选，单平台；缺省检查全部 SAU 平台"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SAU Cookie 状态探测（本地 CLI 或 Sidecar）。"""
    denied = _video_read_guard(current_user)
    if denied:
        return denied
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    names = [platform_name] if platform_name else None
    rows = await sau_check_tenant_platforms(tenant_id=str(tenant_id) if tenant_id else None, platform_names=names)
    ok_count = sum(1 for r in rows if r.get("cookie_ok"))
    return success_response(
        data={
            "tenant_id": str(tenant_id) if tenant_id else None,
            "checked": len(rows),
            "cookie_ok": ok_count,
            "platforms": rows,
        },
        message=f"SAU 账号有效 {ok_count}/{len(rows)}",
    )


class VideoNoteDistributeBody(BaseModel):
    platform_ids: list[str] = Field(default_factory=list)
    image_urls: list[str] = Field(..., min_length=1, max_length=9)
    title: str = Field(..., min_length=1, max_length=120)
    note: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list)
    scheduled_at: datetime | None = None


@router.post("/video/note-distribute")
async def distribute_note_via_sau(
    body: VideoNoteDistributeBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SAU 图文 upload-note（抖音/快手/小红书）。"""
    denied = _video_publish_guard(current_user)
    if denied:
        return denied
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    if not tenant_id:
        return error_response(400, "未绑定租户")

    from app.models.content import Platform
    from app.services.publish_workers.media_fetch import download_image_to_temp
    from app.services.publish_workers.sau_worker import publish_via_sau_note
    from app.services.publish_workers.verify import verify_publish_outcome
    from app.services.video_publish_router import _map_orchestrator_row
    scheduled_ms = None
    if body.scheduled_at is not None:
        dt = body.scheduled_at
        if dt.tzinfo is None:
            from datetime import timezone
            dt = dt.replace(tzinfo=timezone.utc)
        scheduled_ms = int(dt.timestamp() * 1000)

    results: list[dict] = []
    local_images: list = []
    try:
        for url in body.image_urls[:9]:
            local_images.append(await download_image_to_temp(url))
        for pid in body.platform_ids:
            plat = db.query(Platform).filter(Platform.id == pid, Platform.is_active.is_(True)).first()
            if not plat:
                results.append({"platform_id": pid, "success": False, "error_message": "平台不存在"})
                continue
            raw = await publish_via_sau_note(
                platform_name=plat.name,
                local_images=local_images,
                title=body.title,
                note=body.note or body.title,
                tags=body.tags,
                tenant_id=str(tenant_id),
                scheduled_at=scheduled_ms,
            )
            verified = verify_publish_outcome({**raw, "platform_name": plat.name, "tier": "sau"})
            results.append(
                _map_orchestrator_row(verified, platform_id=str(plat.id), platform_name=plat.name)
            )
    finally:
        for p in local_images:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass

    ok = [r for r in results if r.get("success")]
    if not ok and results:
        return error_response(422, "图文分发均未验真成功")
    return success_response(data={"results": results, "summary": {"succeeded": len(ok), "failed": len(results) - len(ok)}})


@router.get("/video/scheduled-queue")
def video_scheduled_queue(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """待发布/已排期任务（PublishTask scheduled_time）。"""
    denied = _video_read_guard(current_user)
    if denied:
        return denied
    from datetime import datetime, timezone
    from app.models.content import PublishTask
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    now = datetime.now(timezone.utc)
    q = db.query(PublishTask).filter(PublishTask.scheduled_time.isnot(None))
    if tenant_id:
        q = q.filter(PublishTask.tenant_id == str(tenant_id))
    rows = q.order_by(PublishTask.scheduled_time.asc()).limit(limit).all()
    items = []
    for t in rows:
        plat_name = None
        if getattr(t, "account", None) and t.account.platform:
            plat_name = t.account.platform.name
        items.append(
            {
                "id": str(t.id),
                "status": t.status,
                "scheduled_time": t.scheduled_time.isoformat() if t.scheduled_time else None,
                "platform_name": plat_name,
                "published_url": t.published_url,
                "is_future": bool(t.scheduled_time and t.scheduled_time > now),
            }
        )
    return success_response(data={"items": items, "total": len(items)})


@router.post("/video/sync-aitoearn")
async def video_sync_aitoearn_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """刷新本租户专属 AiToEarn 代发矩阵到 PlatformAccount。"""
    denied = _video_publish_guard(current_user)
    if denied:
        return denied
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    result = await sync_aitoearn_accounts_to_tenant(db, tenant_id=str(tenant_id))
    if not result.get("ok"):
        msg = result.get("error") or "同步失败"
        if result.get("bind_url"):
            msg = f"{msg}（{result['bind_url']}）"
        return error_response(422, msg)
    return success_response(data=result, message=result.get("message"))


@router.post("/video/admin/assign-aitoearn-slot")
def admin_assign_aitoearn_slot(
    body: AitoearnAssignBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管：为租户独占分配一组 AiToEarn 矩阵号（一租户一 AiToEarn 登录）。"""
    denied = deny_unless_platform_admin(current_user)
    if denied:
        return denied
    result = assign_aitoearn_accounts_to_tenant(
        db,
        tenant_id=body.tenant_id,
        account_ids=body.account_ids,
        bundle_id=body.bundle_id,
        label=body.label,
    )
    if not result.get("ok"):
        return error_response(422, result.get("error") or "分配失败")
    return success_response(data=result, message="AiToEarn 矩阵号已独占分配给租户")


@router.get("/video/admin/aitoearn-pool")
async def admin_aitoearn_pool(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管：查看未分配的 AiToEarn 矩阵账号池。"""
    denied = deny_unless_platform_admin(current_user)
    if denied:
        return denied
    from app.services.tenant_aitoearn_slot_service import list_unassigned_aitoearn_pool
    result = await list_unassigned_aitoearn_pool(db)
    if not result.get("ok"):
        return error_response(503, result.get("error") or "AiToEarn 不可用")
    return success_response(data=result)


@router.post("/video/admin/auto-assign-aitoearn-slot")
def admin_auto_assign_aitoearn_slot(
    tenant_id: str = Query(..., min_length=1, description="租户 UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管：为租户自动分配首个可用 AiToEarn 矩阵号。"""
    denied = deny_unless_platform_admin(current_user)
    if denied:
        return denied
    from app.models.tenant import Tenant
    from app.services.tenant_aitoearn_slot_service import auto_assign_aitoearn_slot_for_tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")
    result = auto_assign_aitoearn_slot_for_tenant(db, tenant)
    if not result.get("ok"):
        return error_response(422, result.get("error") or "自动分配失败")
    return success_response(data=result, message="AiToEarn 矩阵号已自动分配")


@router.get("/video/preflight")

async def video_publish_preflight(

    current_user: User = Depends(get_current_user),

):

    """发布前自检：SAU / biliup / xhs-mcp / AiToEarn Worker 就绪态。"""
    denied = _video_read_guard(current_user)
    if denied:
        return denied

    data = preflight_workers()
    data["browser_companions"] = list_browser_companions(content_type="video")
    data["browser_companion_hint"] = browser_companion_hint(content_type="video")
    return success_response(

        data=data,
        message="Worker 就绪" if data.get("ready") else "Worker 未就绪，请配置 SAU 或 AiToEarn Key",

    )




@router.get("/companion/payload")
def companion_publish_payload(
    companion_id: str = Query(..., description="browser_companion_multipost 等"),
    media_task_id: str | None = Query(None),
    content_id: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """优丁平台专属伴侣载荷 — 须登录且任务归属当前租户，不可匿名拉取。"""
    denied = _video_publish_guard(current_user)
    if denied:
        return denied
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    try:
        if media_task_id:
            payload = build_video_companion_payload(
                db,
                companion_id=companion_id,
                media_task_id=media_task_id,
                tenant_id=str(tenant_id) if tenant_id else None,
            )
        elif content_id:
            payload = build_article_companion_payload(
                db,
                companion_id=companion_id,
                content_id=content_id,
                tenant_id=str(tenant_id) if tenant_id else None,
            )
        else:
            return error_response(400, "请提供 media_task_id 或 content_id")
        meta = companion_launch_meta(companion_id)
    except CompanionLaunchError as exc:
        return error_response(400, str(exc))
    return success_response(data={"meta": meta, "payload": payload})




@router.get("/video/capabilities")

def list_video_publish_capabilities(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """各平台视频真发能力（供前端勾选）。"""
    from app.models.content import Platform
    del current_user
    platforms = db.query(Platform).filter(Platform.is_active.is_(True)).order_by(Platform.name).all()
    items = []
    for p in platforms:

        if (p.content_type or "").find("video") >= 0 or p.name in {

            "YouTube",
            "抖音",
            "快手",
            "哔哩哔哩",
            "微信视频号",
            "TikTok",
            "小红书",

        }:

            pub_key = publisher_key_for_platform(p)
            cap = video_publish_capability(platform_name=p.name, publisher_key=pub_key)
            items.append(

                {

                    "platform_id": str(p.id),
                    "platform_name": p.name,
                    **cap,

                }

            )

    stack = publish_stack_summary()
    return success_response(

        data={

            "hermes_orchestration": True,
            "worker_preflight": stack.get("preflight"),
            "any_worker_ready": stack.get("any_worker_ready"),
            "platforms": items,

        }

    )





@router.post("/video/distribute")

async def distribute_video_api(

    body: VideoDistributeBody,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """统一视频分发：租户官网 + Hermes 多 Worker 真发（须验真链接）。"""
    denied = _video_publish_guard(current_user)
    if denied:
        return denied

    tenant_id = resolve_tenant_id_for_user(db, current_user)
    try:

        data = await distribute_video(

            db,
            media_task_id=body.media_task_id,
            platform_ids=body.platform_ids or None,
            include_tenant_site=body.include_tenant_site,
            tenant_id=tenant_id,
            scheduled_at=body.scheduled_at,

        )

    except ValueError as exc:

        return error_response(400, str(exc))



    summary = data.get("summary") or {}
    msg = data.get("message") or "视频分发完成"
    if summary.get("failed") and not summary.get("succeeded"):

        return error_response(422, msg)

    return success_response(data=data, message=msg)





@router.post("/video/hermes-run")

async def video_matrix_hermes_run(

    body: VideoMatrixHermesBody,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """Hermes 插件 video_matrix_real_publish 同款编排（带步骤轨迹）。"""
    denied = _video_publish_guard(current_user)
    if denied:
        return denied

    tenant_id = resolve_tenant_id_for_user(db, current_user)
    if not tenant_id:

        return error_response(400, "未绑定租户")



    from app.services.hermes.runtime import HermesPluginError, execute_plugin
    try:

        data = execute_plugin(

            db,
            tenant_id=str(tenant_id),
            plugin_id="video_matrix_real_publish",
            message=body.message,
            context={

                "media_task_id": body.media_task_id,
                "platform_ids": body.platform_ids,
                "include_tenant_site": body.include_tenant_site,
                "scheduled_at": body.scheduled_at.isoformat() if body.scheduled_at else None,

            },
            user_id=str(current_user.id) if current_user else None,

        )

    except HermesPluginError as exc:

        return error_response(400, str(exc))



    tool = data.get("tool_result") or {}
    verified = tool.get("verified_posts") or []
    if not verified and (tool.get("distribute") or {}).get("results"):

        return error_response(422, tool.get("reply") or "无验真成功平台")

    return success_response(data=data, message=tool.get("reply") or "Hermes 视频矩阵完成")


