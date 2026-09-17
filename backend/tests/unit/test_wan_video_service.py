# -*- coding: utf-8 -*-
"""阿里 Wan-Video (Wan2.1) 视频生成引擎单测。"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.wan_video_service import (
    enhance_building_materials_prompt,
    is_wan_video_configured,
    render_video_with_wan,
    resolve_dashscope_size,
)


def test_enhance_building_materials_prompt():
    """验证出海建材专用提示词增强效果。"""
    raw_prompt = "豪华石膏板吊顶与铝合金轻钢龙骨施工现场"
    enhanced = enhance_building_materials_prompt(raw_prompt, is_image_to_video=False)
    assert raw_prompt in enhanced
    assert "cinematic architectural commercial lighting" in enhanced
    assert "photorealistic 8k quality" in enhanced


def test_resolve_dashscope_size():
    """验证宽高比与分辨率规范映射。"""
    assert resolve_dashscope_size(aspect="16:9") == "1280*720"
    assert resolve_dashscope_size(aspect="9:16") == "720*1280"
    assert resolve_dashscope_size(aspect="1:1") == "960*960"
    assert resolve_dashscope_size(resolution="480p") == "832*480"


@pytest.mark.asyncio
async def test_render_video_with_wan_fallback(tmp_path: Path):
    """验证在未配置 API Key 和 Sidecar 时走平滑无损降级。"""
    fake_output = tmp_path / "wan_out.mp4"

    with patch("app.services.wan_video_service.get_wan_api_key", return_value=None), \
         patch("app.services.wan_video_service.generate_wan_fallback_video", return_value=True):
        res = await render_video_with_wan(
            prompt="高档瓷砖展示",
            output_path=fake_output,
            model="wanx2.1-t2v-plus",
            resolution="720p",
            aspect="16:9",
        )
        assert res["ok"] is True
        assert res["provider"] == "wan_local_fallback"
        assert res["degraded"] is True


@pytest.mark.asyncio
async def test_render_video_with_wan_dashscope(tmp_path: Path):
    """验证阿里 DashScope Wan2.1 API 提交与下载流水线。"""
    fake_output = tmp_path / "wan_dashscope.mp4"
    fake_bytes = b"fake_mp4_video_content"

    with patch("app.services.wan_video_service.get_wan_api_key", return_value="sk_test_key"), \
         patch("app.services.wan_video_service.submit_dashscope_wan_task", return_value="task_12345"), \
         patch("app.services.wan_video_service.poll_dashscope_task_result", return_value="https://cdn.aliyun.com/wan_video.mp4"), \
         patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = fake_bytes
        mock_get.return_value = mock_resp

        res = await render_video_with_wan(
            prompt="现代轻奢岩板卫浴柜实拍",
            output_path=fake_output,
            model="wanx2.1-t2v-plus",
            resolution="720p",
            aspect="16:9",
        )
        assert res["ok"] is True
        assert res["provider"] == "dashscope_wan2.1"
        assert res["task_id"] == "task_12345"
        assert fake_output.is_file()
        assert fake_output.read_bytes() == fake_bytes
