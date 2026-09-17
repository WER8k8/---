# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""优丁平台专属 · 浏览器伴侣唤起（内容仅来自本平台任务，不可独立外发）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.content import GeneratedContent
from app.services.hermes.browser_companion import is_browser_companion
from app.services.hermes.registry import get_plugin
from app.services.media_factory_service import get_render_task
from app.services.media_publish_service import build_publish_content_from_task


class CompanionLaunchError(ValueError):
    pass


def _plugin_or_raise(companion_id: str) -> dict[str, Any]:
    """_plugin_or_raise。

    参数说明：
    :param companion_id: 参数 companion_id
    :return: 返回处理结果。
    """
    spec = get_plugin(companion_id)
    if not spec or not is_browser_companion(companion_id):
        raise CompanionLaunchError("未知或非浏览器伴侣插件")
    return spec


def build_video_companion_payload(
    db: Session,
    *,
    companion_id: str,
    media_task_id: str,
    tenant_id: str | None,
) -> dict[str, Any]:
    """视频伴侣载荷 — 仅当媒体任务属于当前租户时可取。"""
    _plugin_or_raise(companion_id)
    task = get_render_task(db, media_task_id)
    if not task:
        raise CompanionLaunchError("视频任务不存在")
    if task.status != "done":
        raise CompanionLaunchError("视频尚未渲染完成")
    if tenant_id and task.tenant_id and str(task.tenant_id) != str(tenant_id):
        raise CompanionLaunchError("无权访问该视频任务")

    content = build_publish_content_from_task(task, db=db)
    video_url = (content.get("video_url") or "").strip()
    if not video_url:
        raise CompanionLaunchError("视频尚未上云，无法交给浏览器伴侣")

    title = (content.get("title") or task.title or "视频").strip()
    body = (content.get("body") or "").strip()
    tags = [str(t).strip() for t in (content.get("tags") or []) if str(t).strip()]
    return {
        "platform_bound": True,
        "exclusive_to_youding": True,
        "source": "youding",
        "companion_id": companion_id,
        "launch_kind": "video",
        "media_task_id": media_task_id,
        "tenant_landing_url": content.get("tenant_landing_url"),
        "title": title,
        "body": body,
        "video_url": video_url,
        "tags": tags,
        "multipost": {
            "action": "MULTIPOST_EXTENSION_PUBLISH",
            "sync": {
                "platforms": [],
                "isAutoPublish": False,
                "data": {
                    "title": title,
                    "content": body,
                    "video": {
                        "name": f"youding-{media_task_id[:8]}.mp4",
                        "url": video_url,
                        "type": "video/mp4",
                        "originUrl": video_url,
                    },
                    "tags": tags,
                },
            },
        },
        "usage_notice": (
            "本页内容来自优丁媒体工厂任务，仅供已安装的浏览器伴侣在本平台唤起时使用；"
            "请勿将视频链接复制到其它站点独立发布。"
        ),
    }


def build_article_companion_payload(
    db: Session,
    *,
    companion_id: str,
    content_id: str,
    tenant_id: str | None,
) -> dict[str, Any]:
    """图文伴侣载荷 — SEO 矩阵/草稿正文仅在优丁页内展示供同步。"""
    _plugin_or_raise(companion_id)
    row = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
    if not row:
        raise CompanionLaunchError("内容不存在")

    title = (row.title or "优丁内容").strip()
    body = (row.content or "").strip()
    if not body:
        raise CompanionLaunchError("正文为空")

    return {
        "platform_bound": True,
        "exclusive_to_youding": True,
        "source": "youding",
        "companion_id": companion_id,
        "launch_kind": "article",
        "content_id": content_id,
        "title": title,
        "body_html": body,
        "body_markdown": body,
        "usage_notice": (
            "请在本页使用 Wechatsync 同步到各平台草稿；内容源自优丁，离开本页后伴侣不提供同等能力。"
        ),
    }


def companion_launch_meta(companion_id: str) -> dict[str, Any]:
    """companion_launch_meta。

    参数说明：
    :param companion_id: 参数 companion_id
    :return: 返回处理结果。
    """
    spec = _plugin_or_raise(companion_id)
    pub = spec.get("public") or {}
    companion = pub.get("companion") or {}
    return {
        "companion_id": companion_id,
        "name": pub.get("name"),
        "platform_exclusive": bool(companion.get("platform_exclusive")),
        "launch_route": companion.get("launch_route"),
        "install": companion.get("install") or {},
    }
