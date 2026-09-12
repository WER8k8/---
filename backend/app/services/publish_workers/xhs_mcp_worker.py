"""xiaohongshu-mcp HTTP Worker — 小红书视频真发。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings
from app.services.publish_workers.verify import extract_post_url_from_text


def xhs_mcp_enabled() -> bool:
    """实现 xhsmcpenabled 的功能。
    
    :return: 返回 bool 结果
    """
    return bool(settings.XHS_MCP_ENABLED and (settings.XHS_MCP_BASE_URL or "").strip())


def _base() -> str:
    """实现 base 的功能。
    
    :return: 返回 str 结果
    """
    return (settings.XHS_MCP_BASE_URL or "http://127.0.0.1:18060").rstrip("/")


async def publish_via_xhs_mcp(
    *,
    local_video: Path,
    title: str,
    content: str,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """实现 发布viaxhsmcp 的功能。
    
    :param local_video: 参数 local_video（类型: Path）
    :param title: 参数 title（类型: str）
    :param content: 参数 content（类型: str）
    :param tags: 参数 tags（类型: list[str] | None）
    :return: 返回 dict[str, Any] 结果
    :raises HTTPStatusError: 当操作失败时抛出 HTTPStatusError 异常
    """
    if not xhs_mcp_enabled():
        return {
            "success": False,
            "via": "xhs_mcp",
            "error_message": "未启用 XHS_MCP_BASE_URL（xiaohongshu-mcp 服务）",
        }

    payload = {
        "title": title[:40] or "视频",
        "content": (content or title)[:1000],
        "video": str(local_video.resolve()),
        "tags": tags or [],
    }
    # 优先 REST（vmxmy fork）；404 时尝试 MCP tools/call
    rest_url = f"{_base()}/api/v1/publish_video"
    async with httpx.AsyncClient(timeout=settings.PUBLISH_WORKER_TIMEOUT_SEC) as client:
        try:
            resp = await client.post(rest_url, json=payload)
            if resp.status_code == 404:
                raise httpx.HTTPStatusError("404", request=resp.request, response=resp)
            resp.raise_for_status()
            body = resp.json()
        except httpx.HTTPStatusError:
            mcp_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "publish_with_video",
                    "arguments": {
                        "title": payload["title"],
                        "content": payload["content"],
                        "video": payload["video"],
                        "tags": payload["tags"],
                    },
                },
            }
            resp = await client.post(f"{_base()}/mcp", json=mcp_payload)
            resp.raise_for_status()
            body = resp.json()

    text_blob = str(body)
    post_url = ""
    if isinstance(body, dict):
        for key in ("note_url", "post_url", "url", "share_url", "noteUrl"):
            val = body.get(key) or (body.get("data") or {}).get(key)
            if isinstance(val, str) and val.startswith("http"):
                post_url = val
                break
        if not post_url and isinstance(body.get("result"), dict):
            content_block = body["result"].get("content") or []
            if content_block and isinstance(content_block[0], dict):
                post_url = extract_post_url_from_text(str(content_block[0].get("text") or ""))

    if not post_url:
        post_url = extract_post_url_from_text(text_blob)

    err = ""
    if isinstance(body, dict):
        err = str(body.get("error") or body.get("message") or "")

    return {
        "via": "xhs_mcp",
        "raw_output": text_blob[:4000],
        "platform_post_url": post_url,
        "platform_post_id": "",
        "success": False,
        "error_message": err[:500] if err and not post_url else None,
    }
