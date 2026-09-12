"""统一视频发布口 — Hermes 双线编排：主路 SAU + 备路 AiToEarn + 强制验真。"""

from __future__ import annotations

import asyncio
import concurrent.futures
from datetime import datetime, timezone
from typing import Any

from app.services.media_factory_service import get_render_task
from app.services.media_publish_service import build_publish_content_from_task
from app.services.media_tenant_traffic_service import get_tenant, publish_video_to_tenant_site
from app.services.platform_account_service import (
    account_configs,
    find_tenant_platform_account,
    resolve_platform_for_publish,
)
from app.services.publish_capability_registry import (
    is_publish_result_success,
    publish_block_reason,
    video_publish_capability,
)
from app.services.publish_dispatch_service import publisher_key_for_platform
from app.services.publish_service import PublishService
from app.services.publish_workers.dual_line import dual_line_block_reason, dual_line_status
from app.services.publish_workers.tier_router import platform_tier_chain, preflight_workers_async
from app.services.video_publish_orchestrator import publish_platform_video


def _safe_asyncio_run(coro):
    """安全执行异步协程：兼容已有事件循环（FastAPI）和无事件循环（Celery）。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def credentials_from_account(account, configs: dict[str, str]) -> dict[str, Any]:
    """credentials_from_account。

    参数说明：
    :param account: 参数 account
    :param configs: 参数 configs
    :return: 返回处理结果。
    """
    creds: dict[str, Any] = {}
    td = account.token_data
    if isinstance(td, dict):
        creds.update(td)
    if account.cookie_data:
        creds["cookies"] = account.cookie_data
    for key in ("access_token", "appid", "appsecret", "password", "page_access_token"):
        if configs.get(key):
            creds[key] = configs[key]
    if isinstance(td, dict) and td.get("access_token"):
        creds["access_token"] = td["access_token"]
    return creds


async def _publish_youtube_native(
    *,
    content: dict[str, Any],
    account,
    configs: dict[str, str],
) -> dict[str, Any]:
    """_publish_youtube_native。

    参数说明：
    :param content: 参数 content
    :param account: 参数 account
    :param configs: 参数 configs
    :return: 返回处理结果。
    """
    creds = credentials_from_account(account, configs)
    if not creds.get("access_token"):
        return {
            "success": False,
            "error_message": "YouTube 账号未配置 OAuth access_token",
            "via": "native_youtube",
        }
    base = next((p for p in PublishService().platforms if p["id"] == "youtube"), None)
    if not base:
        return {"success": False, "error_message": "YouTube 平台配置缺失", "via": "native_youtube"}
    cfg = {**base, "credentials": creds}
    from app.services.publish_service import PUBLISHER_MAP
    pub = PUBLISHER_MAP["youtube"](cfg)
    outcome = await pub.publish(content)
    ok = is_publish_result_success(outcome)
    return {
        "success": ok,
        "verified": ok,
        "platform_post_url": outcome.get("platform_post_url"),
        "platform_post_id": outcome.get("platform_post_id"),
        "error_message": outcome.get("error_message")
        or (None if ok else "YouTube 发布未返回作品链接"),
        "via": "native_youtube",
        "tier": "native_youtube",
        "publish_line": "primary" if ok else "none",
    }


def _map_orchestrator_row(
    row: dict[str, Any],
    *,
    platform_id: str,
    platform_name: str,
) -> dict[str, Any]:
    """_map_orchestrator_row。

    参数说明：
    :param row: 参数 row
    :param platform_id: 参数 platform_id
    :param platform_name: 参数 platform_name
    :return: 返回处理结果。
    """
    verified = bool(row.get("verified")) and bool(row.get("success"))
    return {
        "platform_id": platform_id,
        "platform_name": platform_name,
        "success": verified,
        "verified": verified,
        "platform_post_url": row.get("platform_post_url"),
        "platform_post_id": row.get("platform_post_id"),
        "flow_id": row.get("flow_id"),
        "error_message": row.get("error_message"),
        "via": row.get("via") or row.get("tier"),
        "tier": row.get("tier"),
        "attempts": row.get("attempts"),
        "verify_hint": row.get("verify_hint"),
        "publish_line": row.get("publish_line"),
        "failover": row.get("failover"),
        "primary_line_error": row.get("primary_line_error"),
    }


def _resolve_scheduled_ms(scheduled_at: datetime | None) -> int | None:
    """把 scheduled_at 归一化为毫秒时间戳。"""
    if scheduled_at is None:
        return None
    dt = scheduled_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _publish_video_to_tenant_site(
    db: Session,
    task: Any,
    *,
    include_tenant_site: bool,
    scope_tenant: str | None,
) -> dict[str, Any]:
    """按开关把视频登记到租户官网。"""
    if not include_tenant_site:
        return {"published": False}
    tenant = get_tenant(db, scope_tenant or task.tenant_id)
    if not tenant:
        return {"published": False}
    return publish_video_to_tenant_site(db, task, tenant)


def _resolve_platform_names(db: Session, ids: list[str]) -> list[str]:
    """把平台 ID 列表解析为平台名列表（跳过不存在的平台）。"""
    names: list[str] = []
    for pid in ids:
        plat = resolve_platform_for_publish(db, pid)
        if plat:
            names.append(plat.name)
    return names


def _resolve_allowed_aitoearn_ids(db: Session, scope_tenant: str | None) -> set[str] | None:
    """解析该租户允许使用的 AiToEarn 账号白名单。"""
    if not scope_tenant:
        return None
    tenant_row = get_tenant(db, scope_tenant)
    if not tenant_row:
        return None
    from app.services.tenant_aitoearn_slot_service import get_tenant_aitoearn_account_ids
    aids = get_tenant_aitoearn_account_ids(tenant_row)
    return set(aids) if aids else None


async def _call_orchestrator(
    *,
    platform: Any,
    video_url: str,
    cover_url: str,
    title: str,
    body: str,
    tags: list[Any],
    scope_tenant: str | None,
    allowed_aito: set[str] | None,
    scheduled_ms: int | None,
) -> dict[str, Any]:
    """调用双线编排器发布，并把结果行映射为统一结构。"""
    from app.services.media.platform_title_adapt import adapt_title
    row = await publish_platform_video(
        platform_name=platform.name,
        video_url=video_url,
        cover_url=cover_url,
        title=adapt_title(title, platform.name),
        body=body,
        tags=tags,
        tenant_id=scope_tenant,
        allowed_aitoearn_ids=allowed_aito,
        scheduled_at=scheduled_ms,
    )
    return _map_orchestrator_row(
        row,
        platform_id=str(platform.id),
        platform_name=platform.name,
    )


async def _distribute_youtube_platform(
    db: Session,
    *,
    platform: Any,
    content: dict[str, Any],
    video_url: str,
    cover_url: str,
    title: str,
    body: str,
    tags: list[Any],
    scope_tenant: str | None,
    allowed_aito: set[str] | None,
    scheduled_ms: int | None,
) -> tuple[dict[str, Any], bool]:
    """处理 YouTube 平台分发，返回 (结果行, 是否命中原生 OAuth 通道)。"""
    account = find_tenant_platform_account(
        db,
        tenant_id=scope_tenant,
        platform_id=str(platform.id),
        prefer_logged_in=True,
    )
    if account and account.login_status == "logged_in":
        configs = account_configs(db, account)
        native = await _publish_youtube_native(content=content, account=account, configs=configs)
        return (
            {
                "platform_id": str(platform.id),
                "platform_name": platform.name,
                **native,
            },
            True,
        )

    if platform_tier_chain(platform.name):
        row = await _call_orchestrator(
            platform=platform,
            video_url=video_url,
            cover_url=cover_url,
            title=title,
            body=body,
            tags=tags,
            scope_tenant=scope_tenant,
            allowed_aito=allowed_aito,
            scheduled_ms=scheduled_ms,
        )
        return row, False

    return (
        {
            "platform_id": str(platform.id),
            "platform_name": platform.name,
            "success": False,
            "verified": False,
            "error_message": "YouTube 需 OAuth 登录或配置发布 Worker",
            "via": "blocked",
        },
        False,
    )


async def _distribute_generic_platform(
    *,
    platform: Any,
    content: dict[str, Any],
    blocked: str | None,
    cap: dict[str, Any],
    video_url: str,
    cover_url: str,
    title: str,
    body: str,
    tags: list[Any],
    scope_tenant: str | None,
    allowed_aito: set[str] | None,
    scheduled_ms: int | None,
) -> dict[str, Any]:
    """处理非 YouTube 平台分发。"""
    if blocked:
        return {
            "platform_id": str(platform.id),
            "platform_name": platform.name,
            "success": False,
            "verified": False,
            "error_message": blocked,
            "via": "blocked",
            "video_publish_tier": cap.get("tier"),
        }

    if not platform_tier_chain(platform.name):
        return {
            "platform_id": str(platform.id),
            "platform_name": platform.name,
            "success": False,
            "verified": False,
            "error_message": cap.get("reason")
            or f"{platform.name} 无可用发布 Worker，请配置 SAU 主路 + AiToEarn 备路",
            "via": "blocked",
        }

    return await _call_orchestrator(
        platform=platform,
        video_url=video_url,
        cover_url=cover_url,
        title=title,
        body=body,
        tags=tags,
        scope_tenant=scope_tenant,
        allowed_aito=allowed_aito,
        scheduled_ms=scheduled_ms,
    )


def _build_distribute_response(
    *,
    media_task_id: str,
    video_url: str,
    content: dict[str, Any],
    site_result: dict[str, Any],
    worker_preflight: Any,
    dual_line: Any,
    youtube_handled: bool,
    results: list[dict[str, Any]],
    ids: list[str],
    scope_tenant: str | None,
) -> dict[str, Any]:
    """汇总分发结果、发送通知并构造最终响应。"""
    succeeded = [r for r in results if r.get("success") and r.get("verified")]
    failed = [r for r in results if not r.get("success")]
    failover_wins = [r for r in succeeded if r.get("failover")]
    overall = bool(succeeded) and (not failed or site_result.get("published"))
    from app.services.publish_result_notify_service import notify_video_distribute_summary
    notify_video_distribute_summary(
        tenant_id=scope_tenant,
        media_task_id=media_task_id,
        summary={
            "succeeded": len(succeeded),
            "failed": len(failed),
            "failover_succeeded": len(failover_wins),
            "overall_success": overall,
        },
        results=results,
    )
    return {
        "media_task_id": media_task_id,
        "publish_video_url": video_url,
        "tenant_landing_url": content.get("tenant_landing_url"),
        "tenant_site": site_result,
        "worker_preflight": worker_preflight,
        "dual_line": dual_line,
        "hermes_orchestration": True,
        "youtube_native_available": youtube_handled,
        "results": results,
        "summary": {
            "requested": len(ids),
            "succeeded": len(succeeded),
            "failed": len(failed),
            "failover_succeeded": len(failover_wins),
            "overall_success": overall,
        },
        "message": (
            f"视频分发：验真成功 {len(succeeded)}（备路救回 {len(failover_wins)}）/ 失败 {len(failed)}"
            if results
            else "已登记租户官网；未选择外站平台"
        ),
    }


async def distribute_video(
    db: Session,
    *,
    media_task_id: str,
    platform_ids: list[str] | None = None,
    include_tenant_site: bool = True,
    tenant_id: str | None = None,
    scheduled_at: datetime | None = None,
) -> dict[str, Any]:
    """唯一视频分发入口：官网 + 双线 failover 真发 + 验真。"""
    scheduled_ms = _resolve_scheduled_ms(scheduled_at)
    task = get_render_task(db, media_task_id)
    if not task:
        raise ValueError("任务不存在")
    if task.status != "done":
        raise ValueError("任务尚未渲染完成")

    content = build_publish_content_from_task(task, db=db)
    video_url = content.get("video_url") or ""
    if not video_url:
        raise ValueError("视频尚未上云，无法外站真发")

    cover_url = task.image_url or task.cloud_play_url or video_url
    scope_tenant = tenant_id or (str(task.tenant_id) if task.tenant_id else None)
    site_result = _publish_video_to_tenant_site(
        db,
        task,
        include_tenant_site=include_tenant_site,
        scope_tenant=scope_tenant,
    )
    ids = [p for p in (platform_ids or []) if (p or "").strip()]
    platform_names = _resolve_platform_names(db, ids)
    dual_block = dual_line_block_reason(platform_names=platform_names)
    if dual_block:
        raise ValueError(dual_block)

    results: list[dict[str, Any]] = []
    youtube_handled = False
    worker_preflight = await preflight_workers_async()
    dual_line = dual_line_status()
    title = content.get("title") or task.title or "视频"
    body = content.get("body") or ""
    tags = list(content.get("tags") or [])
    allowed_aito = _resolve_allowed_aitoearn_ids(db, scope_tenant)
    for pid in ids:
        platform = resolve_platform_for_publish(db, pid)
        if not platform:
            results.append(
                {
                    "platform_id": pid,
                    "success": False,
                    "verified": False,
                    "error_message": "平台不存在",
                }
            )
            continue

        pub_key = publisher_key_for_platform(platform)
        cap = video_publish_capability(platform_name=platform.name, publisher_key=pub_key)
        blocked = publish_block_reason(
            platform_name=platform.name,
            publisher_key=pub_key,
            content=content,
        )
        if platform.name == "YouTube" or pub_key == "youtube":
            row, handled = await _distribute_youtube_platform(
                db,
                platform=platform,
                content=content,
                video_url=video_url,
                cover_url=cover_url,
                title=title,
                body=body,
                tags=tags,
                scope_tenant=scope_tenant,
                allowed_aito=allowed_aito,
                scheduled_ms=scheduled_ms,
            )
            results.append(row)
            if handled:
                youtube_handled = True
            continue

        results.append(
            await _distribute_generic_platform(
                platform=platform,
                content=content,
                blocked=blocked,
                cap=cap,
                video_url=video_url,
                cover_url=cover_url,
                title=title,
                body=body,
                tags=tags,
                scope_tenant=scope_tenant,
                allowed_aito=allowed_aito,
                scheduled_ms=scheduled_ms,
            )
        )

    return _build_distribute_response(
        media_task_id=media_task_id,
        video_url=video_url,
        content=content,
        site_result=site_result,
        worker_preflight=worker_preflight,
        dual_line=dual_line,
        youtube_handled=youtube_handled,
        results=results,
        ids=ids,
        scope_tenant=scope_tenant,
    )


def distribute_video_sync(db: Session, **kwargs: Any) -> dict[str, Any]:
    """distribute_video_sync。

    参数说明：
    :param db: 参数 db
    :param **kwargs: 参数 **kwargs
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(distribute_video(db, **kwargs))
