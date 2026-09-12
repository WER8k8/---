"""多媒体工厂 → 多平台发布（带 video_url，不破坏 SEO 正文）。"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any

from sqlalchemy.orm import Session

from app.models.media_factory import MediaRenderTask
from app.services.media_cloud_upload_service import overseas_publish_video_url, playback_url_for_task
from app.services.media_factory_service import get_render_task
from app.services.media_seo_service import build_media_seo_bundle, upsert_media_seo_metadata
from app.services.media_tenant_traffic_service import (
    build_platform_description,
    get_tenant,
    publish_video_to_tenant_site,
)
from app.models.content import Platform
from app.services.platform_account_service import (
    find_tenant_platform_account,
    resolve_platform_for_publish,
)
from app.services.publish_capability_registry import (
    is_publish_result_success,
    publish_block_reason,
)
from app.services.publish_dispatch_service import (
    SeoPublishService,
    publisher_key_for_platform,
)
from app.services.publish_service import PublishService


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


def build_publish_content_from_task(
    task: MediaRenderTask,
    *,
    db: Session | None = None,
    seo_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """build_publish_content_from_task。

    参数说明：
    :param task: 参数 task
    :param db: 参数 db
    :param seo_bundle: 参数 seo_bundle
    :return: 返回处理结果。
    """
    video_url = overseas_publish_video_url(task) or playback_url_for_task(task)
    if not video_url:
        raise ValueError("视频尚未就绪（请等待上云完成或检查 cloud_upload_status）")

    bundle = seo_bundle or build_media_seo_bundle(task)
    tenant = get_tenant(db, task.tenant_id) if db else None
    if db and tenant:
        site_bundle = publish_video_to_tenant_site(db, task, tenant)
        bundle = {**bundle, **{k: v for k, v in site_bundle.items() if k not in ("published", "reason")}}

    body_text = bundle.get("meta_description") or ""
    if tenant:
        body_text = build_platform_description(task, tenant, bundle)

    return {
        "title": task.title or "视频",
        "body": body_text,
        "video_url": video_url,
        "tags": list((bundle.get("geo_facts") or [])[:8]),
        "media_render_task_id": task.id,
        "seo_bundle": bundle,
        "tenant_landing_url": bundle.get("tenant_landing_url"),
    }


async def publish_task_to_platforms(
    task: MediaRenderTask,
    platform_ids: list[str],
    *,
    db: Session | None = None,
    persist_seo: bool = True,
) -> list[dict[str, Any]]:
    """publish_task_to_platforms。

    参数说明：
    :param task: 参数 task
    :param platform_ids: 参数 platform_ids
    :param db: 参数 db
    :param persist_seo: 参数 persist_seo
    :return: 返回处理结果。
    """
    bundle = build_media_seo_bundle(task)
    if persist_seo and db is not None:
        upsert_media_seo_metadata(db, task, bundle)

    content = build_publish_content_from_task(task, db=db, seo_bundle=bundle)
    async_svc = PublishService()
    seo_svc = SeoPublishService(db) if db is not None else None
    tenant_id = str(task.tenant_id) if task.tenant_id else None
    results: list[dict[str, Any]] = []
    for platform_id in platform_ids:
        pid = (platform_id or "").strip()
        if not pid:
            continue
        try:
            platform: Platform | None = None
            account = None
            if db is not None:
                platform = resolve_platform_for_publish(db, pid)
                if platform:
                    account = find_tenant_platform_account(
                        db,
                        tenant_id=tenant_id,
                        platform_id=str(platform.id),
                        prefer_logged_in=True,
                    )

            pub_key = publisher_key_for_platform(platform) if platform else pid
            blocked = publish_block_reason(
                platform_name=platform.name if platform else None,
                publisher_key=pub_key,
                content=content,
            )
            if blocked:
                raise RuntimeError(blocked)

            if platform and account and account.login_status == "logged_in" and seo_svc:
                post_url = seo_svc.dispatch_media_content(platform, account, content)
                if not (post_url or "").strip():
                    raise RuntimeError(f"{platform.name} 发布未返回作品链接，视为失败")
                results.append(
                    {
                        "platform_id": pid,
                        "platform_name": platform.name,
                        "success": True,
                        "verified": True,
                        "platform_post_url": post_url,
                        "via": "bound_account",
                    }
                )
                continue

            outcome = await async_svc.publish(pub_key, content)
            ok = is_publish_result_success(outcome)
            results.append(
                {
                    "platform_id": pid,
                    "platform_name": platform.name if platform else None,
                    "success": ok,
                    "verified": ok,
                    "platform_post_url": outcome.get("platform_post_url"),
                    "error_message": outcome.get("error_message")
                    or (None if ok else "发布未返回作品链接，视为失败"),
                    "via": "platform_config",
                }
            )
        except Exception as exc:
            pname = None
            if db is not None:
                plat = resolve_platform_for_publish(db, pid)
                pname = plat.name if plat else None
            results.append(
                {
                    "platform_id": pid,
                    "platform_name": pname,
                    "success": False,
                    "error_message": str(exc),
                }
            )
    return results


def publish_task_to_platforms_sync(
    db: Session,
    task_id: str,
    platform_ids: list[str],
) -> dict[str, Any]:
    """publish_task_to_platforms_sync。

    参数说明：
    :param db: 参数 db
    :param task_id: 参数 task_id
    :param platform_ids: 参数 platform_ids
    :return: 返回处理结果。
    """
    task = get_render_task(db, task_id)
    if not task:
        raise ValueError("任务不存在")
    if task.status != "done":
        raise ValueError("任务尚未渲染完成")
    results = asyncio.run(publish_task_to_platforms(task, platform_ids, db=db))
    content = build_publish_content_from_task(task, db=db)
    return {
        "task_id": task_id,
        "publish_video_url": overseas_publish_video_url(task) or playback_url_for_task(task),
        "tenant_landing_url": content.get("tenant_landing_url"),
        "results": results,
        "seo_bundle": content.get("seo_bundle") or build_media_seo_bundle(task),
    }


async def publish_video_traffic_funnel(
    db: Session,
    task_id: str,
    platform_ids: list[str] | None = None,
) -> dict[str, Any]:
    """完整引流：租户官网落地页（SEO/GEO）+ 可选视频网站发布。"""
    task = get_render_task(db, task_id)
    if not task:
        raise ValueError("任务不存在")
    if task.status != "done":
        raise ValueError("任务尚未渲染完成")

    tenant = get_tenant(db, task.tenant_id)
    site_result: dict[str, Any] = {"published": False}
    if tenant:
        site_result = publish_video_to_tenant_site(db, task, tenant)
    else:
        site_result = {"published": False, "reason": "no_tenant"}

    platform_results: list[dict[str, Any]] = []
    if platform_ids:
        platform_results = await publish_task_to_platforms(
            task, platform_ids, db=db, persist_seo=False
        )

    content = build_publish_content_from_task(task, db=db)
    return {
        "task_id": task_id,
        "tenant_site": site_result,
        "platform_results": platform_results,
        "tenant_landing_url": content.get("tenant_landing_url"),
        "publish_video_url": overseas_publish_video_url(task) or playback_url_for_task(task),
        "seo_bundle": content.get("seo_bundle"),
        "message": "已登记租户视频页；视频网站发布结果见 platform_results",
    }


def publish_video_traffic_funnel_sync(
    db: Session,
    task_id: str,
    platform_ids: list[str] | None = None,
) -> dict[str, Any]:
    """publish_video_traffic_funnel_sync。

    参数说明：
    :param db: 参数 db
    :param task_id: 参数 task_id
    :param platform_ids: 参数 platform_ids
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(publish_video_traffic_funnel(db, task_id, platform_ids))
