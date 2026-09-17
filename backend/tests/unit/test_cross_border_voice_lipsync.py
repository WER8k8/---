# -*- coding: utf-8 -*-
"""出海视音频数字人工厂（多语种原声克隆 & 嘴型对齐）单测。"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.routes.cross_border import VideoDubBody, PremiumDubBody, AutoDistributeBody
from app.services.cross_border.voice_cloning_service import (
    TARGET_LANG_MAP,
    synthesize_voice_cloned_audio,
)
from app.services.cross_border.lipsync_service import apply_video_lipsync
from app.services.cross_border.video_dub_service import _translate_script, _format_srt


def test_target_lang_map_12_languages():
    """验证 12 大出海目标国家语言映射表完整性。"""
    expected_langs = ["en", "ar", "es", "ru", "pt", "fr", "de", "ja", "ko", "vi", "id", "th"]
    assert len(TARGET_LANG_MAP) == 12
    for lang in expected_langs:
        assert lang in TARGET_LANG_MAP
        info = TARGET_LANG_MAP[lang]
        assert "name" in info
        assert "en_name" in info
        assert "flag" in info
        assert "edge_tts" in info


def test_video_dub_body_defaults():
    """验证 VideoDubBody 默认启用声线克隆、嘴型对齐与 12 语种扩展。"""
    body = VideoDubBody(media_task_id="task_123")
    assert body.target_lang == "en"
    assert body.voice_clone is True
    assert body.lip_sync is True
    assert body.distribute_platforms is None


def test_premium_dub_body_custom():
    """验证 PremiumDubBody 自定义语种与分发平台。"""
    body = PremiumDubBody(
        media_task_id="task_456",
        target_lang="es",
        voice_clone=True,
        lip_sync=True,
        distribute_platforms=["youtube", "tiktok", "instagram"],
    )
    assert body.target_lang == "es"
    assert body.distribute_platforms == ["youtube", "tiktok", "instagram"]


def test_format_srt_multilingual():
    """验证多语种分段字幕 SRT 格式化。"""
    segs = [
        {
            "start": "00:00:00,000",
            "end": "00:00:04,500",
            "text_ar": "نحن مصنع محترف لمواد البناء",
            "text_en": "We are a professional building materials factory",
        }
    ]
    srt = _format_srt(segs, target_lang="ar")
    assert "00:00:00,000 --> 00:00:04,500" in srt
    assert "نحن مصنع محترف لمواد البناء" in srt


@pytest.mark.asyncio
async def test_voice_cloning_fallback(tmp_path: Path):
    """验证无 GPU Sidecar 时平滑降级至神经语音。"""
    fake_source = tmp_path / "video.mp4"
    fake_source.write_bytes(b"dummy")
    fake_out = tmp_path / "out.mp3"

    with patch("app.services.cross_border.voice_cloning_service.extract_reference_audio", return_value=False):
        res = await synthesize_voice_cloned_audio(
            text="Hello world",
            source_media_path=fake_source,
            target_lang="en",
            output_mp3_path=fake_out,
            voice_clone_enabled=True,
        )
        assert res["cloned"] is False
        assert "provider" in res


@pytest.mark.asyncio
async def test_lipsync_fallback(tmp_path: Path):
    """验证无 GPU Lipsync 时平滑降级至 smart mux。"""
    fake_video = tmp_path / "video.mp4"
    fake_audio = tmp_path / "audio.mp3"
    fake_out = tmp_path / "out.mp4"
    fake_video.write_bytes(b"dummy")
    fake_audio.write_bytes(b"dummy")

    with patch("app.services.cross_border.lipsync_service.apply_ffmpeg_smart_mux", return_value=True):
        res = await apply_video_lipsync(
            source_video_path=fake_video,
            audio_path=fake_audio,
            output_video_path=fake_out,
            lipsync_enabled=True,
        )
        assert res["ok"] is True
        assert res["engine"] == "standard_mux"
