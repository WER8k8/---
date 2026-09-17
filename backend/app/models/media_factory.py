# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""多媒体工厂：渲染任务模型。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import UUID_TYPE, Base


class MediaRenderTask(Base):
    __tablename__ = "media_render_tasks"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False, default="未命名任务")
    task_type = Column(String(30), nullable=False, default="video")
    script = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="queued", index=True)
    progress = Column(Integer, nullable=False, default=0)
    priority = Column(String(10), nullable=False, default="中")
    scenario = Column(String(64), default="article_to_video_render")
    prompt_text = Column(Text)
    video_model = Column(String(120))
    voice = Column(String(50))
    resolution = Column(String(20))
    aspect = Column(String(20))
    image_url = Column(String(500))
    result_url = Column(String(500))
    result_path = Column(String(500))
    tenant_id = Column(String(36), index=True)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    purge_at = Column(DateTime(timezone=True))
    handoff_type = Column(String(20))
    handoff_at = Column(DateTime(timezone=True))
    handoff_external_url = Column(String(500))
    file_purged = Column(Integer, default=0, nullable=False)  # 0/1 SQLite 友好
    edit_config = Column(Text)
    edited_result_path = Column(String(500))
    edited_result_url = Column(String(500))
    guest_token = Column(String(64), index=True)
    cloud_provider = Column(String(20))
    cloud_vid = Column(String(64))
    cloud_play_url = Column(String(500))
    cloud_r2_key = Column(String(500))
    cloud_r2_url = Column(String(1000))
    cloud_backup_url = Column(String(500))
    cloud_upload_status = Column(String(20), default="pending", index=True)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
