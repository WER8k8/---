"""MOSS-VL AI 剪辑与一键分发联动工作流（集成 SEO/GEO/AAO 排名自动增强）。"""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.moss_auto_clip_pipeline import MossAutoClipPipeline
from app.services.moss_vl_service import MossVLService

logger = logging.getLogger(__name__)


@dataclass
class PublishDispatchResult:
    """单个切片的分发状态（附带 SEO/GEO/AAO 增强参数）。"""
    clip_id: str
    platform: str
    status: str
    title: str
    task_id: str
    target_video: str
    pinned_comment: str
    seo_keywords: list[str]
    geo_summary: str


class MossClipAndPublishWorkflow:
    """智能剪辑与一键分发编排器。"""

    def __init__(
        self,
        clip_pipeline: MossAutoClipPipeline | None = None,
        moss_service: MossVLService | None = None,
    ):
        self.moss_service = moss_service or MossVLService()
        self.clip_pipeline = clip_pipeline or MossAutoClipPipeline(moss_service=self.moss_service)

    def run_clip_and_publish_workflow(
        self,
        video_path_or_url: str,
        target_platforms: list[str],
        tenant_id: str = "default_tenant",
        video_duration_sec: float | None = 120.0,
        auto_dispatch: bool = True,
    ) -> dict[str, Any]:
        """一键全流程：长视频 -> MOSS 自动切片 -> 挂载 SEO/GEO/AAO 排名优化 -> 一键分发。"""
        clip_result = self.clip_pipeline.execute_auto_clip_pipeline(
            video_path_or_url=video_path_or_url,
            video_duration_sec=video_duration_sec,
            target_platforms=target_platforms,
        )

        clips_data = clip_result.get("clips", [])
        dispatch_records: list[PublishDispatchResult] = []

        for clip in clips_data:
            clip_id = clip.get("clip_id", "clip_000")
            video_file = clip.get("clip_video_path", "")
            platform_meta = clip.get("platform_metadata", {})

            for platform in target_platforms:
                meta = platform_meta.get(platform, {})
                title = meta.get("title", f"精选高光片段 {clip_id}")
                pinned_comment = meta.get("pinned_comment", "")
                seo_keywords = meta.get("seo_keywords", [])
                geo_summary = meta.get("geo_summary", "")

                task_id = f"pub_{uuid.uuid4().hex[:12]}"
                
                dispatch_records.append(
                    PublishDispatchResult(
                        clip_id=clip_id,
                        platform=platform,
                        status="queued" if auto_dispatch else "draft",
                        title=title,
                        task_id=task_id,
                        target_video=video_file,
                        pinned_comment=pinned_comment,
                        seo_keywords=seo_keywords,
                        geo_summary=geo_summary,
                    )
                )

        return {
            "workflow_id": f"wf_{uuid.uuid4().hex[:10]}",
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_video": video_path_or_url,
            "total_clips_generated": len(clips_data),
            "target_platforms": target_platforms,
            "ranking_enhancement_active": True,
            "clips": clips_data,
            "dispatched_tasks": [asdict(r) for r in dispatch_records],
            "status": "completed",
        }
