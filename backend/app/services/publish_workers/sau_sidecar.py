# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SAU HTTP Sidecar 客户端 — 远程 Worker 机执行 Playwright 上传。"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx

from app.core.config import settings
from app.services.cross_border.sidecar_health import probe_sidecar_health


def sau_sidecar_enabled() -> bool:
    """实现 sausidecarenabled 的功能。
    
    :return: 返回 bool 结果
    """
    return bool((settings.SAU_SIDECAR_URL or "").strip())


def sau_sidecar_base() -> str:
    """实现 sausidecarbase 的功能。
    
    :return: 返回 str 结果
    """
    return (settings.SAU_SIDECAR_URL or "").strip().rstrip("/")


def sau_sidecar_health() -> dict[str, Any]:
    """实现 sausidecarhealth 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    base = sau_sidecar_base()
    if not base:
        return {"ok": False, "reason": "SAU_SIDECAR_URL not set"}
    return probe_sidecar_health(base)


async def submit_sau_publish_job(payload: dict[str, Any]) -> dict[str, Any]:
    """POST /api/youding/sau/publish → { job_id, status }。"""
    base = sau_sidecar_base()
    if not base:
        raise RuntimeError("未配置 SAU_SIDECAR_URL")
    url = urljoin(base + "/", "/api/youding/sau/publish")
    timeout = float(settings.PUBLISH_WORKER_TIMEOUT_SEC or 900)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    if not isinstance(data, dict):
        raise RuntimeError("SAU sidecar 返回非 JSON 对象")
    return data


async def poll_sau_publish_job(job_id: str, *, poll_interval: float = 2.0) -> dict[str, Any]:
    """GET /api/youding/sau/jobs/{id} 直到 done/failed 或超时。"""
    import asyncio
    base = sau_sidecar_base()
    if not base:
        raise RuntimeError("未配置 SAU_SIDECAR_URL")
    url = urljoin(base + "/", f"/api/youding/sau/jobs/{job_id}")
    deadline = asyncio.get_event_loop().time() + float(settings.PUBLISH_WORKER_TIMEOUT_SEC or 900)
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        while asyncio.get_event_loop().time() < deadline:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                raise RuntimeError("SAU sidecar job 返回异常")
            status = str(data.get("status") or "").lower()
            if status in ("done", "failed"):
                return data
            await asyncio.sleep(poll_interval)
    raise RuntimeError(f"SAU sidecar job {job_id} 轮询超时")


async def publish_via_sau_sidecar(
    *,
    platform_name: str,
    tenant_id: str | None,
    title: str,
    desc: str,
    tags: list[str] | None,
    local_video: Path | None = None,
    local_images: list[Path] | None = None,
    cover_path: Path | None = None,
    scheduled_at: Any = None,
    bilibili_tid: int | None = None,
    mode: str = "video",
    video_url: str = "",
    cover_url: str = "",
) -> dict[str, Any]:
    """实现 发布viasausidecar 的功能。
    
    :param platform_name: 参数 platform_name（类型: str）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param title: 参数 title（类型: str）
    :param desc: 参数 desc（类型: str）
    :param tags: 参数 tags（类型: list[str] | None）
    :param local_video: 参数 local_video（类型: Path | None）
    :param local_images: 参数 local_images（类型: list[Path] | None）
    :param cover_path: 参数 cover_path（类型: Path | None）
    :param scheduled_at: 参数 scheduled_at（类型: Any）
    :param bilibili_tid: 参数 bilibili_tid（类型: int | None）
    :param mode: 参数 mode（类型: str）
    :param video_url: 参数 video_url（类型: str）
    :param cover_url: 参数 cover_url（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    from app.services.publish_workers.sau_worker import format_sau_schedule, sau_account_name
    account = sau_account_name(tenant_id=tenant_id, platform_name=platform_name)
    payload: dict[str, Any] = {
        "platform_name": platform_name,
        "account": account,
        "title": title[:120] or "视频",
        "desc": (desc or title)[:500],
        "tags": tags or [],
        "mode": mode,
        "schedule": format_sau_schedule(scheduled_at),
        "bilibili_tid": bilibili_tid,
        "video_url": (video_url or "").strip(),
        "cover_url": (cover_url or "").strip(),
    }
    if local_video and local_video.exists():
        payload["video_path"] = str(local_video)
    if local_images:
        payload["image_paths"] = [str(p) for p in local_images if p.exists()]
    if cover_path and cover_path.exists():
        payload["cover_path"] = str(cover_path)

    queued = await submit_sau_publish_job(payload)
    job_id = queued.get("job_id")
    if not job_id:
        return {
            "success": False,
            "via": "sau_sidecar",
            "error_message": queued.get("error") or "sidecar 未返回 job_id",
        }
    result = await poll_sau_publish_job(str(job_id))
    if str(result.get("status")).lower() == "failed":
        return {
            "success": False,
            "via": "sau_sidecar",
            "job_id": job_id,
            "error_message": (result.get("error") or "sidecar 发布失败")[:500],
        }
    outcome = dict(result.get("result") or {})
    outcome["via"] = "sau_sidecar"
    outcome["job_id"] = job_id
    return outcome


async def sau_check_via_sidecar(*, platform_name: str, account: str) -> dict[str, Any]:
    """实现 sau检查viasidecar 的功能。
    
    :param platform_name: 参数 platform_name（类型: str）
    :param account: 参数 account（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    base = sau_sidecar_base()
    if not base:
        return {"ok": False, "reason": "SAU_SIDECAR_URL not set"}
    url = urljoin(base + "/", "/api/youding/sau/check")
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        resp = await client.post(url, json={"platform_name": platform_name, "account": account})
        if resp.status_code != 200:
            return {"ok": False, "reason": f"http_{resp.status_code}"}
        data = resp.json()
    if isinstance(data, dict):
        return data
    return {"ok": False, "reason": "bad_json"}
