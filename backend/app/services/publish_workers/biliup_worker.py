"""biliup CLI Worker — B站专用，可解析 BV 回执。"""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.publish_workers.verify import extract_bvid_from_text, extract_post_url_from_text


def biliup_cli_path() -> str:
    """实现 biliupclipath 的功能。
    
    :return: 返回 str 结果
    """
    custom = (settings.BILIUP_CLI_PATH or "").strip()
    if custom:
        return custom
    for name in ("biliup", "biliupR", "biliup.exe", "biliupR.exe"):
        found = shutil.which(name)
        if found:
            return found
    return ""


def biliup_enabled() -> bool:
    """实现 biliupenabled 的功能。
    
    :return: 返回 bool 结果
    """
    if not settings.BILIUP_ENABLED:
        return False
    return bool(biliup_cli_path())


async def publish_via_biliup(
    *,
    local_video: Path,
    title: str,
    desc: str,
    tags: list[str] | None = None,
    cookie_file: str | None = None,
) -> dict[str, Any]:
    """实现 发布viabiliup 的功能。
    
    :param local_video: 参数 local_video（类型: Path）
    :param title: 参数 title（类型: str）
    :param desc: 参数 desc（类型: str）
    :param tags: 参数 tags（类型: list[str] | None）
    :param cookie_file: 参数 cookie_file（类型: str | None）
    :return: 返回 dict[str, Any] 结果
    """
    cli = biliup_cli_path()
    if not cli:
        return {
            "success": False,
            "via": "biliup",
            "error_message": "未找到 biliup CLI，请安装 biliup 或配置 BILIUP_CLI_PATH",
        }

    cookie = cookie_file or settings.BILIUP_COOKIE_FILE or "cookies.json"
    tag_str = ",".join(tags or []) or "视频"
    cmd = [
        cli,
        "upload",
        str(local_video),
        "--title",
        title[:80] or "视频",
        "--desc",
        (desc or title)[:250],
        "--tid",
        str(settings.SAU_BILIBILI_TID),
        "--tags",
        tag_str,
        "--user-cookie",
        cookie,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(),
            timeout=settings.PUBLISH_WORKER_TIMEOUT_SEC,
        )
    except asyncio.TimeoutError:
        proc.kill()
        return {"success": False, "via": "biliup", "error_message": "biliup 上传超时"}

    merged = f"{stdout_b.decode('utf-8', errors='replace')}\n{stderr_b.decode('utf-8', errors='replace')}"
    post_url = extract_post_url_from_text(merged)
    bvid = extract_bvid_from_text(merged)
    if bvid and not post_url:
        post_url = f"https://www.bilibili.com/video/{bvid}"

    outcome: dict[str, Any] = {
        "via": "biliup",
        "exit_code": proc.returncode or 0,
        "raw_output": merged[:4000],
        "platform_post_url": post_url,
        "platform_post_id": bvid or "",
        "success": False,
    }
    if proc.returncode != 0:
        outcome["error_message"] = merged[:500] or "biliup 上传失败"
    return outcome
