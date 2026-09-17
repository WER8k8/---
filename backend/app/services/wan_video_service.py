# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""阿里 Wan-Video (Wan2.1) 视频生成专有引擎 — 文生视频 (T2V) & 图生视频 (I2V)。

对标并超越传统渲染，支持：
1. 阿里官方百炼 (DashScope) Wan2.1 API (wanx2.1-t2v-plus / wanx2.1-t2v-turbo / wanx2.1-i2v-plus)；
2. PPIO 云 / Serverless GPU 端点 (Wan2.1-14B / Wan2.1-1.3B)；
3. Wan-Video 开源私有 Docker Sidecar (WAN_VIDEO_BASE_URL)；
4. 外贸建材工业品专用 Prompt 增强器 (光影、材质反射、细节纹理、电影级运镜)；
5. 无 GPU 算力时的平滑无损降级。
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Callable

import httpx

from app.core.config import settings
from app.core.executable_resolver import resolve_executable
from app.core.uploads_path import UPLOADS_DIR, ensure_uploads_dir

logger = logging.getLogger(__name__)

# 阿里 DashScope 官方默认端点
DASHSCOPE_ASYNC_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
DASHSCOPE_TASK_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/tasks"

# 分辨率预设对照
RESOLUTION_MAP = {
    "1080p": {"width": 1280, "height": 720, "dashscope_size": "1280*720"},
    "720p": {"width": 1280, "height": 720, "dashscope_size": "1280*720"},
    "480p": {"width": 832, "height": 480, "dashscope_size": "832*480"},
}

ASPECT_MAP = {
    "16:9": "1280*720",
    "9:16": "720*1280",
    "1:1": "960*960",
}


def is_wan_video_configured() -> bool:
    """检查是否配置了可用的 Wan-Video 上游（DashScope / PPIO / 私有 Sidecar）。"""
    if getattr(settings, "WAN_VIDEO_BASE_URL", None) or os.getenv("WAN_VIDEO_BASE_URL"):
        return True
    if getattr(settings, "AI_DASHSCOPE_API_KEY", None) or os.getenv("AI_DASHSCOPE_API_KEY"):
        return True
    if getattr(settings, "WAN_VIDEO_API_KEY", None) or os.getenv("WAN_VIDEO_API_KEY"):
        return True
    if os.getenv("PPIO_API_KEY"):
        return True
    return False


def get_wan_api_key() -> str | None:
    """获取 Wan-Video 可用的 API Key。"""
    return (
        getattr(settings, "WAN_VIDEO_API_KEY", None)
        or os.getenv("WAN_VIDEO_API_KEY")
        or getattr(settings, "AI_DASHSCOPE_API_KEY", None)
        or os.getenv("AI_DASHSCOPE_API_KEY")
        or os.getenv("PPIO_API_KEY")
        or ""
    ).strip() or None


def enhance_building_materials_prompt(
    prompt: str,
    resolution: str = "720p",
    aspect: str = "16:9",
    is_image_to_video: bool = False,
) -> str:
    """针对出海建材与工业产品进行专业 Prompt 增强。"""
    raw = (prompt or "").strip()
    if not raw:
        raw = "High-end modern building materials showroom with architectural samples and elegant textures."

    # 提炼工业品质感词
    enhancers = [
        "cinematic architectural commercial lighting",
        "ultra-detailed surface textures",
        "smooth camera slow pan",
        "clean studio presentation",
        "photorealistic 8k quality",
        "flawless industrial design",
    ]
    if is_image_to_video:
        enhancers.append("subtle realistic motion, smooth rotation, dynamic light reflections")
    else:
        enhancers.append("showcase the craftsmanship, material durability, and export-grade finishing")

    return f"{raw}, {', '.join(enhancers)}"


def resolve_dashscope_size(resolution: str | None = None, aspect: str | None = None) -> str:
    """将分辨率与宽高比转换为 DashScope Wan2.1 规范的 size 参数。"""
    res_key = (resolution or "").lower()
    asp_key = (aspect or "").strip()

    if res_key == "480p":
        if asp_key == "9:16":
            return "480*832"
        if asp_key == "1:1":
            return "624*624"
        return "832*480"

    if asp_key in ASPECT_MAP:
        return ASPECT_MAP[asp_key]
    if res_key in RESOLUTION_MAP:
        return RESOLUTION_MAP[res_key]["dashscope_size"]
    return "1280*720"


async def submit_dashscope_wan_task(
    *,
    prompt: str,
    model: str = "wanx2.1-t2v-plus",
    image_url: str | None = None,
    size: str = "1280*720",
    duration_sec: int = 5,
    api_key: str,
) -> str | None:
    """向阿里百炼 DashScope 异步提交 Wan2.1 视频生成任务，返回 task_id。"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }

    payload: dict[str, Any] = {
        "model": model,
        "input": {
            "prompt": prompt,
        },
        "parameters": {
            "size": size,
            "duration": duration_sec,
        },
    }

    # 如果有图片输入，自动走图生视频 (I2V)
    if image_url:
        payload["model"] = "wanx2.1-i2v-plus" if "plus" in model else "wanx2.1-i2v-turbo"
        payload["input"]["img_url"] = image_url

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(DASHSCOPE_ASYNC_ENDPOINT, json=payload, headers=headers)
            if resp.status_code in (200, 201, 202):
                data = resp.json()
                task_id = data.get("output", {}).get("task_id")
                if task_id:
                    logger.info("DashScope Wan2.1 task submitted: %s", task_id)
                    return str(task_id)
            logger.warning("DashScope Wan2.1 submission failed: %s %s", resp.status_code, resp.text)
    except Exception as exc:
        logger.warning("DashScope Wan2.1 error: %s", exc)
    return None


async def poll_dashscope_task_result(
    task_id: str,
    api_key: str,
    timeout_sec: int = 600,
    on_progress: Callable[[int, str], None] | None = None,
) -> str | None:
    """轮询阿里 DashScope 视频任务状态直至完成，返回生成的视频公网 URL。"""
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{DASHSCOPE_TASK_ENDPOINT}/{task_id}"
    start_time = time.time()

    while time.time() - start_time < timeout_sec:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("output", {}).get("task_status")
                    if status == "SUCCEEDED":
                        video_url = data.get("output", {}).get("video_url")
                        if video_url:
                            logger.info("Wan2.1 video generation succeeded: %s", video_url)
                            return str(video_url)
                    elif status == "FAILED":
                        error_msg = data.get("output", {}).get("message", "Task failed")
                        logger.error("Wan2.1 task %s failed: %s", task_id, error_msg)
                        return None

                    if on_progress:
                        elapsed = int(time.time() - start_time)
                        progress = min(90, max(20, 20 + elapsed // 4))
                        on_progress(progress, f"阿里 Wan2.1 正在生成视频帧（已耗时 {elapsed}s）…")
        except Exception as exc:
            logger.warning("poll_dashscope_task_result error: %s", exc)

        await asyncio.sleep(5)
    return None


async def call_sidecar_wan_video(
    sidecar_url: str,
    prompt: str,
    image_url: str | None = None,
    resolution: str = "720p",
    aspect: str = "16:9",
) -> bytes | None:
    """调用私有部署的 Wan-Video (Wan2.1) GPU Sidecar 容器。"""
    url = f"{sidecar_url.rstrip('/')}/v1/video/generations"
    payload = {
        "prompt": prompt,
        "image_url": image_url,
        "resolution": resolution,
        "aspect": aspect,
    }
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200 and resp.content:
                return resp.content
    except Exception as exc:
        logger.warning("call_sidecar_wan_video error: %s", exc)
    return None


def generate_wan_fallback_video(
    output_path: Path,
    title: str = "YouDing Premium Building Materials",
    resolution: str = "720p",
    aspect: str = "16:9",
) -> bool:
    """平滑降级：FFmpeg 本地极速合成优雅的建材展示动态视频。"""
    ffmpeg = resolve_executable("ffmpeg")
    if not ffmpeg:
        return False
    size = RESOLUTION_MAP.get(resolution, RESOLUTION_MAP["720p"])
    w, h = size["width"], size["height"]
    if aspect == "9:16":
        w, h = 720, 1280

    safe_title = title.replace("'", "").replace(":", "").replace("\\", "")[:40] or "YouDing Building Materials"
    cmd = [
        ffmpeg,
        "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0f172a:s={w}x{h}:d=5:r=24",
        "-vf",
        (
            f"drawbox=y=0:color=0x4a9b8c@0.3:width=iw:height=6:t=fill,"
            f"drawtext=text='YouDing Wan-Video Engine':fontcolor=0x4a9b8c:fontsize=28:x=40:y=40,"
            f"drawtext=text='{safe_title}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2,"
            f"drawtext=text='Export Grade Photorealistic Presentation':fontcolor=0x94a3b8:fontsize=20:x=(w-text_w)/2:y=(h-text_h)/2+60"
        ),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-t", "5",
        str(output_path),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=60)
        return proc.returncode == 0 and output_path.is_file() and output_path.stat().st_size > 1024
    except Exception as exc:
        logger.warning("generate_wan_fallback_video error: %s", exc)
        return False


async def render_video_with_wan(
    *,
    prompt: str,
    output_path: Path,
    image_url: str | None = None,
    model: str = "wanx2.1-t2v-plus",
    resolution: str = "720p",
    aspect: str = "16:9",
    on_progress: Callable[[int, str], None] | None = None,
) -> dict[str, Any]:
    """Wan-Video (Wan2.1) 最优解主渲染执行流。"""
    ensure_uploads_dir()
    enhanced_prompt = enhance_building_materials_prompt(
        prompt, resolution=resolution, aspect=aspect, is_image_to_video=bool(image_url)
    )
    api_key = get_wan_api_key()
    sidecar_url = (getattr(settings, "WAN_VIDEO_BASE_URL", None) or os.getenv("WAN_VIDEO_BASE_URL") or "").strip()

    # 1. 尝试私有 GPU Sidecar
    if sidecar_url:
        if on_progress:
            on_progress(25, "调用私有 GPU Sidecar Wan-Video 模型生成视频…")
        raw_bytes = await call_sidecar_wan_video(
            sidecar_url, enhanced_prompt, image_url=image_url, resolution=resolution, aspect=aspect
        )
        if raw_bytes:
            output_path.write_bytes(raw_bytes)
            return {
                "ok": True,
                "provider": "wan_video_sidecar",
                "model": "wan2.1-14b-local",
                "prompt": enhanced_prompt,
                "output_path": str(output_path),
            }

    # 2. 尝试阿里 DashScope 官方 Wan2.1 API
    if api_key:
        if on_progress:
            on_progress(20, "已提交至阿里 DashScope Wan2.1 引擎…")
        size = resolve_dashscope_size(resolution=resolution, aspect=aspect)
        task_id = await submit_dashscope_wan_task(
            prompt=enhanced_prompt,
            model=model,
            image_url=image_url,
            size=size,
            duration_sec=5,
            api_key=api_key,
        )
        if task_id:
            remote_url = await poll_dashscope_task_result(task_id, api_key=api_key, on_progress=on_progress)
            if remote_url:
                if on_progress:
                    on_progress(90, "下载 Wan2.1 渲染成片至本地…")
                # 下载视频至本地 output_path
                async with httpx.AsyncClient(timeout=120) as client:
                    resp = await client.get(remote_url)
                    if resp.status_code == 200 and resp.content:
                        output_path.write_bytes(resp.content)
                        return {
                            "ok": True,
                            "provider": "dashscope_wan2.1",
                            "model": model,
                            "task_id": task_id,
                            "prompt": enhanced_prompt,
                            "remote_url": remote_url,
                            "output_path": str(output_path),
                        }

    # 3. 降级兜底：FFmpeg 本地极速动态占位
    if on_progress:
        on_progress(85, "未配置 GPU/API Key，使用本地建材动态渲染器出片…")
    ok = generate_wan_fallback_video(output_path, title=prompt[:40], resolution=resolution, aspect=aspect)
    if ok:
        return {
            "ok": True,
            "provider": "wan_local_fallback",
            "model": "wan_ffmpeg_presentation",
            "degraded": True,
            "prompt": enhanced_prompt,
            "output_path": str(output_path),
        }

    return {"ok": False, "error": "Wan-Video 视频渲染失败"}
