# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""视频任务 SEO / GEO 增强：独立 VideoObject，不覆盖文章页既有 Schema。"""

from __future__ import annotations

import json
import re
from typing import Any

from app.models.media_factory import MediaRenderTask
from app.models.seo_metadata import SeoMetadata
from app.models.seo_metadata import SEOMetadata
from app.services.media_cloud_upload_service import overseas_publish_video_url, playback_url_for_task
from sqlalchemy.orm import Session

_SHOT_PREFIX = re.compile(r"^\s*(?:镜头|镜|Scene)\s*\d+", re.I)


def _excerpt(text: str, max_len: int = 160) -> str:
    """_excerpt。

    参数说明：
    :param text: 参数 text
    :param max_len: 参数 max_len
    :return: 返回处理结果。
    """
    flat = " ".join((text or "").split())
    if len(flat) <= max_len:
        return flat
    return flat[: max_len - 1].rstrip() + "…"


def _geo_facts_from_script(script: str, limit: int = 5) -> list[str]:
    """供 GEO / AI 引用的要点（不写入 Article 正文 Schema）。"""
    facts: list[str] = []
    for line in (script or "").splitlines():
        line = line.strip()
        if not line or _SHOT_PREFIX.match(line):
            continue
        if "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            line = parts[-1] if parts else line
        if len(line) < 8:
            continue
        facts.append(line[:240])
        if len(facts) >= limit:
            break
    return facts


def build_media_seo_bundle(
    task: MediaRenderTask,
    *,
    canonical_path: str | None = None,
    site_base_url: str = "",
) -> dict[str, Any]:
    """生成视频页专用 SEO 包；**禁止**合并进 unrelated Article/Product 的 schema_markup。"""
    playback = playback_url_for_task(task) or ""
    publish_url = overseas_publish_video_url(task) or playback
    description = _excerpt(task.script)
    upload_date = task.finished_at.isoformat() if task.finished_at else None
    video_ld: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": task.title or "视频",
        "description": description,
        "uploadDate": upload_date,
    }
    if publish_url:
        video_ld["contentUrl"] = publish_url
    if playback:
        video_ld["embedUrl"] = playback

    base = (site_base_url or "").rstrip("/")
    path = canonical_path or f"/videos/{task.id}"
    canonical = f"{base}{path}" if base else path
    if canonical:
        video_ld["url"] = canonical

    og_tags = {
        "og:type": "video.other",
        "og:title": (task.title or "视频")[:200],
        "og:description": description,
    }
    if playback:
        og_tags["og:video"] = playback
        og_tags["og:video:type"] = "video/mp4"

    return {
        "media_task_id": task.id,
        "meta_title": (task.title or "视频")[:60],
        "meta_description": description,
        "canonical_url": canonical,
        "playback_url": playback,
        "publish_video_url": publish_url,
        "og_tags": og_tags,
        "video_object": video_ld,
        "schema_markup_json": json.dumps(video_ld, ensure_ascii=False),
        "geo_facts": _geo_facts_from_script(task.script),
        "seo_note": (
            "VideoObject 仅用于视频落地页或发布元数据；"
            "勿注入县域 SEO 文章页，避免与 Article/FAQ Schema 冲突。"
        ),
    }


def upsert_media_seo_metadata(
    db: Session, task: MediaRenderTask, bundle: dict[str, Any]
) -> SEOMetadata | SeoMetadata:
    """为视频任务单独登记 SEO 元数据（entity_type=media_video，与文章页 Schema 隔离）。"""
    task_id = str(task.id)
    row = (
        db.query(SEOMetadata)
        .filter(
            SEOMetadata.entity_type == "media_video",
            SEOMetadata.entity_id == task_id,
        )
        .first()
    )
    schema_json = bundle.get("schema_markup_json")
    og = bundle.get("og_tags") or {}
    if not row:
        import uuid as _uuid
        row = SEOMetadata(
            id=str(_uuid.uuid4()),
            entity_type="media_video",
            entity_id=task_id,
        )
        db.add(row)
    row.meta_title = bundle.get("meta_title")
    row.meta_description = bundle.get("meta_description")
    row.canonical_url = bundle.get("canonical_url")
    row.og_title = bundle.get("meta_title")
    row.og_description = bundle.get("meta_description")
    row.og_image = og.get("og:image")
    row.structured_data = schema_json
    legacy = (
        db.query(SeoMetadata)
        .filter(
            SeoMetadata.resource_type == "media_video",
            SeoMetadata.resource_id == task_id,
        )
        .first()
    )
    if legacy is not None:
        legacy.meta_title = row.meta_title
        legacy.meta_description = row.meta_description
        legacy.canonical_url = row.canonical_url
        legacy.og_title = row.og_title
        legacy.og_description = row.og_description
        legacy.og_image = row.og_image
        legacy.schema_markup = schema_json
        legacy.noindex = False
        legacy.robots = "index,follow,max-video-preview:-1"
        db.add(legacy)

    db.add(row)
    db.commit()
    db.refresh(row)
    return row
