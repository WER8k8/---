"""§2 视频平台格式自适应单元测试。

只测纯函数（spec 常量 / 判定 / 命令构造），不依赖真实 ffmpeg，
保证 CI 无媒体环境也能过。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.platform_video_adapter import (
    PLATFORM_VIDEO_SPECS,
    VideoSpec,
    _build_ffmpeg_cmd,
    _plan_adaptation,
    auto_adapt,
)


class TestSpecConstants:
    def test_all_specs_are_frozen(self):
        for spec in PLATFORM_VIDEO_SPECS.values():
            assert isinstance(spec, VideoSpec)
            with pytest.raises(Exception):
                spec.max_duration_sec = 999

    def test_key_platforms_present(self):
        for key in ("tiktok", "instagram_reels", "youtube_shorts", "youtube"):
            assert key in PLATFORM_VIDEO_SPECS

    def test_shorts_max_60s(self):
        assert PLATFORM_VIDEO_SPECS["youtube_shorts"].max_duration_sec == 60

    def test_tiktok_max_600s(self):
        assert PLATFORM_VIDEO_SPECS["tiktok"].max_duration_sec == 600


class TestPlanAdaptation:
    def test_normal_no_change(self):
        spec = PLATFORM_VIDEO_SPECS["tiktok"]
        src = {"duration_sec": 120, "width": 1080, "height": 1920, "size_mb": 50}
        assert _plan_adaptation(spec, src) == []

    def test_duration_over_triggers_trim(self):
        spec = PLATFORM_VIDEO_SPECS["youtube_shorts"]  # 60s cap
        src = {"duration_sec": 90, "width": 1080, "height": 1920, "size_mb": 5}
        plans = _plan_adaptation(spec, src)
        assert any("trim_duration" in p for p in plans)

    def test_size_over_triggers_compress(self):
        spec = PLATFORM_VIDEO_SPECS["tiktok"]  # 288MB cap
        src = {"duration_sec": 60, "width": 1080, "height": 1920, "size_mb": 400}
        plans = _plan_adaptation(spec, src)
        assert "reencode_compress" in plans

    def test_landscape_to_916_triggers_pad(self):
        spec = PLATFORM_VIDEO_SPECS["youtube_shorts"]
        src = {"duration_sec": 30, "width": 1920, "height": 1080, "size_mb": 5}
        plans = _plan_adaptation(spec, src)
        assert "pad_to_9x16" in plans

    def test_unknown_duration_no_trim(self):
        spec = PLATFORM_VIDEO_SPECS["tiktok"]
        src = {"duration_sec": 0, "width": 1080, "height": 1920, "size_mb": 10}
        assert "trim" not in " ".join(_plan_adaptation(spec, src))


class TestBuildFfmpegCmd:
    def test_pad_cmd_contains_vf_pad(self):
        spec = PLATFORM_VIDEO_SPECS["youtube_shorts"]
        src = {"duration_sec": 30, "width": 1920, "height": 1080, "size_mb": 5}
        cmd = _build_ffmpeg_cmd(spec, src, Path("in.mp4"), Path("out.mp4"))
        joined = " ".join(cmd)
        assert "pad" in joined and "black" in joined

    def test_compress_cmd_sets_bitrate(self):
        spec = PLATFORM_VIDEO_SPECS["tiktok"]
        src = {"duration_sec": 60, "width": 1080, "height": 1920, "size_mb": 400}
        cmd = _build_ffmpeg_cmd(spec, src, Path("in.mp4"), Path("out.mp4"))
        assert "-b:v" in cmd

    def test_trim_cmd_has_duration_flag(self):
        spec = PLATFORM_VIDEO_SPECS["youtube_shorts"]
        src = {"duration_sec": 90, "width": 1080, "height": 1920, "size_mb": 5}
        cmd = _build_ffmpeg_cmd(spec, src, Path("in.mp4"), Path("out.mp4"))
        assert "-t" in cmd and "60" in cmd


class TestAutoAdapt:
    def test_unsupported_platform(self, tmp_path: Path):
        v = tmp_path / "x.mp4"
        v.write_bytes(b"x")
        r = auto_adapt(v, "no_such_platform")
        assert r.adapted is False
        assert "unsupported" in r.reason

    def test_missing_ffprobe_degrades(self, tmp_path: Path, monkeypatch):
        v = tmp_path / "x.mp4"
        v.write_bytes(b"fake")
        monkeypatch.setattr(
            "app.services.platform_video_adapter._which",
            lambda b: (str(tmp_path / b) if b == "ffmpeg" else None),
        )
        r = auto_adapt(v, "tiktok")
        assert r.ffmpeg_ok is False
        assert "ffprobe_missing" in r.reason or "ffmpeg_missing" in r.reason
