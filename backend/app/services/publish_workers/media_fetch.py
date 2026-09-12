"""将云视频 URL 拉到 Worker 本地路径（SAU / xhs-mcp 需要本地文件）。"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


def _guess_suffix(url: str) -> str:
    """实现 guesssuffix 的功能。
    
    :param url: 参数 url（类型: str）
    :return: 返回 str 结果
    """
    path = urlparse(url).path.lower()
    for ext in (".mp4", ".mov", ".webm", ".mkv"):
        if path.endswith(ext):
            return ext
    return ".mp4"


async def download_video_to_temp(video_url: str, *, timeout: float = 120.0) -> Path:
    """实现 下载视频totemp 的功能。
    
    :param video_url: 参数 video_url（类型: str）
    :param timeout: 参数 timeout（类型: float）
    :return: 返回 Path 结果
    :raises ValueError: 当操作失败时抛出 ValueError 异常
    :raises RuntimeError: 当操作失败时抛出 RuntimeError 异常
    """
    url = (video_url or "").strip()
    if not url.startswith("http"):
        raise ValueError("video_url 无效")
    suffix = _guess_suffix(url)
    tmp_dir = Path(tempfile.gettempdir()) / "youding_publish"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / f"pub_{uuid.uuid4().hex[:12]}{suffix}"
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        async with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as fh:
                async for chunk in resp.aiter_bytes(chunk_size=1024 * 256):
                    fh.write(chunk)
    if dest.stat().st_size < 1024:
        dest.unlink(missing_ok=True)
        raise RuntimeError("下载的视频文件过小或为空")
    logger.info("publish media fetched size=%s path=%s", dest.stat().st_size, dest.name)
    return dest


def _guess_image_suffix(url: str) -> str:
    """实现 guess图片suffix 的功能。
    
    :param url: 参数 url（类型: str）
    :return: 返回 str 结果
    """
    path = urlparse(url).path.lower()
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        if path.endswith(ext):
            return ext
    return ".jpg"


async def download_image_to_temp(image_url: str, *, timeout: float = 60.0) -> Path:
    """实现 下载图片totemp 的功能。
    
    :param image_url: 参数 image_url（类型: str）
    :param timeout: 参数 timeout（类型: float）
    :return: 返回 Path 结果
    :raises ValueError: 当操作失败时抛出 ValueError 异常
    :raises RuntimeError: 当操作失败时抛出 RuntimeError 异常
    """
    url = (image_url or "").strip()
    if not url.startswith("http"):
        raise ValueError("cover_url 无效")
    suffix = _guess_image_suffix(url)
    tmp_dir = Path(tempfile.gettempdir()) / "youding_publish"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / f"cover_{uuid.uuid4().hex[:12]}{suffix}"
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        async with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as fh:
                async for chunk in resp.aiter_bytes(chunk_size=1024 * 64):
                    fh.write(chunk)
    if dest.stat().st_size < 256:
        dest.unlink(missing_ok=True)
        raise RuntimeError("下载的封面过小或为空")
    return dest
