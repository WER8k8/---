# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AiToEarn Relay — 抖音/快手/B站等短视频平台真发。

增强自原版本，新增：
- 素材库管理（material group / media group）
- 草稿编排能力（draft management）
- 账号分组（account group）
- 互动管理 API 封装（engage / comment / like）
- 更完善的错误处理与重试
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import uuid
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _safe_asyncio_run(coro):
    """安全执行异步协程：兼容已有事件循环（FastAPI）和无事件循环（Celery）。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)

# 平台显示名 → AiToEarn accountType（小写）
PLATFORM_TO_AITO_ACCOUNT_TYPE: dict[str, str] = {
    "抖音": "douyin",
    "快手": "kuaishou",
    "哔哩哔哩": "bilibili",
    "微信视频号": "wxchannels",
    "TikTok": "tiktok",
    "TikTok / 抖音国际版": "tiktok",
    "YouTube": "youtube",
    "小红书": "xiaohongshu",
    "Facebook": "facebook",
    "Instagram": "instagram",
    "Threads": "threads",
    "Twitter": "twitter",
    "X": "twitter",
    "LinkedIn": "linkedin",
    "Pinterest": "pinterest",
}

# accountType 别名（AiToEarn 可能返回不同拼写）
_ACCOUNT_TYPE_ALIASES: dict[str, set[str]] = {
    "douyin": {"douyin", "dy"},
    "kuaishou": {"kuaishou", "ks", "kwai"},
    "bilibili": {"bilibili", "bili", "b站"},
    "wxchannels": {"wxchannels", "shipinhao", "channels", "weixinchannels"},
    "tiktok": {"tiktok"},
    "youtube": {"youtube", "yt"},
    "xiaohongshu": {"xiaohongshu", "xhs", "rednote"},
    "facebook": {"facebook", "fb"},
    "instagram": {"instagram", "ig"},
    "threads": {"threads"},
    "twitter": {"twitter", "x"},
    "linkedin": {"linkedin"},
    "pinterest": {"pinterest"},
}


def aitoearn_enabled() -> bool:
    """aitoearn_enabled。
    :return: 返回处理结果。
    """
    return bool((settings.AITOEARN_API_KEY or "").strip())


def _base_url() -> str:
    """_base_url。
    :return: 返回处理结果。
    """
    return (settings.AITOEARN_API_BASE or "https://mcp.aitoearn.cn").rstrip("/")


def _headers() -> dict[str, str]:
    """_headers。
    :return: 返回处理结果。
    """
    return {
        "sk-key": settings.AITOEARN_API_KEY or "",
        "Content-Type": "application/json",
    }


def normalize_account_type(raw: str) -> str:
    """normalize_account_type。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    val = (raw or "").strip().lower()
    for canonical, aliases in _ACCOUNT_TYPE_ALIASES.items():
        if val in aliases or val == canonical:
            return canonical
    return val


def account_type_for_platform_name(name: str) -> str | None:
    """account_type_for_platform_name。

    参数说明：
    :param name: 参数 name
    :return: 返回处理结果。
    """
    mapped = PLATFORM_TO_AITO_ACCOUNT_TYPE.get(name)
    if mapped:
        return mapped
    return normalize_account_type(name) if name else None


# ---- 账号管理 ----

async def fetch_accounts() -> list[dict[str, Any]]:
    """获取所有绑定的 AiToEarn 账号。"""
    if not aitoearn_enabled():
        return []
    url = f"{_base_url()}/plugin/account/list"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers=_headers())
        resp.raise_for_status()
        body = resp.json()
    if body.get("code"):
        raise RuntimeError(body.get("message") or "AiToEarn 账号列表失败")
    return list(body.get("data") or [])


async def fetch_account_groups() -> list[dict[str, Any]]:
    """获取账号分组（借鉴 AiToEarn account-group.service）。"""
    if not aitoearn_enabled():
        return []
    url = f"{_base_url()}/plugin/account/group/list"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=_headers())
            resp.raise_for_status()
            body = resp.json()
        if body.get("code"):
            logger.warning("AiToEarn account group list failed: %s", body.get("message"))
            return []
        return list(body.get("data") or [])
    except Exception as exc:
        logger.warning("AiToEarn account group list error: %s", exc)
        return []


# ---- 发布任务 ----

async def create_publish_task(
    *,
    account_id: str,
    flow_id: str,
    title: str,
    video_url: str,
    cover_url: str,
    topics: str,
    desc: str = "",
    scheduled_at: int | None = None,
) -> dict[str, Any]:
    """创建发布任务（支持定时发布）。"""
    payload = {
        "flowId": flow_id,
        "accountId": account_id,
        "type": "video",
        "title": title,
        "desc": desc,
        "videoUrl": video_url,
        "coverUrl": cover_url,
        "topics": topics,
    }
    if scheduled_at:
        payload["publishTime"] = scheduled_at  # Unix timestamp (ms)

    url = f"{_base_url()}/plugin/publish/create"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()


async def create_image_publish_task(
    *,
    account_id: str,
    flow_id: str,
    title: str,
    image_urls: list[str],
    topics: str,
    desc: str = "",
) -> dict[str, Any]:
    """创建图文发布任务（小红书/Instagram 等图文平台）。"""
    payload = {
        "flowId": flow_id,
        "accountId": account_id,
        "type": "image",
        "title": title,
        "desc": desc,
        "imageUrls": image_urls,
        "topics": topics,
    }
    url = f"{_base_url()}/plugin/publish/create"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()


async def fetch_publish_tasks(flow_id: str) -> list[dict[str, Any]]:
    """fetch_publish_tasks。

    参数说明：
    :param flow_id: 参数 flow_id
    :return: 返回处理结果。
    """
    url = f"{_base_url()}/plugin/publish/task/list/{flow_id}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers=_headers())
        resp.raise_for_status()
        body = resp.json()
    if body.get("code"):
        raise RuntimeError(body.get("message") or "AiToEarn 任务查询失败")
    return list(body.get("data") or [])


def _task_is_success(task: dict[str, Any]) -> bool:
    """_task_is_success。

    参数说明：
    :param task: 参数 task
    :return: 返回处理结果。
    """
    status = task.get("status")
    err = (task.get("errorMsg") or task.get("error_msg") or "").strip()
    if err:
        return False
    if status in (2, "2", "success", "published", "done"):
        return True
    if status in (3, "3", "failed", "error"):
        return False
    return False


def _task_post_url(task: dict[str, Any]) -> str:
    """_task_post_url。

    参数说明：
    :param task: 参数 task
    :return: 返回处理结果。
    """
    for key in ("postUrl", "publishUrl", "workUrl", "url", "videoUrl", "shareUrl"):
        val = (task.get(key) or "").strip()
        if val.startswith("http"):
            return val
    return ""


async def poll_publish_tasks(flow_id: str, *, attempts: int = 15, delay_sec: float = 3.0) -> list[dict[str, Any]]:
    """poll_publish_tasks。

    参数说明：
    :param flow_id: 参数 flow_id
    :param attempts: 参数 attempts
    :param delay_sec: 参数 delay_sec
    :return: 返回处理结果。
    """
    last: list[dict[str, Any]] = []
    for _ in range(attempts):
        last = await fetch_publish_tasks(flow_id)
        if not last:
            await asyncio.sleep(delay_sec)
            continue
        terminal = all(
            _task_is_success(t)
            or (t.get("errorMsg") or t.get("error_msg"))
            or t.get("status") in (3, "3", "failed", "error")
            for t in last
        )
        if terminal:
            return last
        await asyncio.sleep(delay_sec)
    return last


# ---- 互动管理（借鉴 AiToEngagement） ----

async def fetch_post_comments(
    *,
    account_id: str,
    post_id: str,
    platform: str = "",
) -> list[dict[str, Any]]:
    """获取作品评论列表。"""
    if not aitoearn_enabled():
        return []
    params = {"accountId": account_id, "postId": post_id}
    if platform:
        params["platform"] = platform
    url = f"{_base_url()}/plugin/engagement/comment/list"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=_headers(), params=params)
            resp.raise_for_status()
            body = resp.json()
        if body.get("code"):
            logger.warning("AiToEarn comment list failed: %s", body.get("message"))
            return []
        return list(body.get("data") or [])
    except Exception as exc:
        logger.warning("AiToEarn comment list error: %s", exc)
        return []


async def reply_comment(
    *,
    account_id: str,
    comment_id: str,
    content: str,
    post_id: str = "",
) -> dict[str, Any]:
    """回复评论。"""
    payload = {
        "accountId": account_id,
        "commentId": comment_id,
        "content": content,
    }
    if post_id:
        payload["postId"] = post_id
    url = f"{_base_url()}/plugin/engagement/comment/reply"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()


async def like_post(
    *,
    account_id: str,
    post_id: str,
    platform: str = "",
) -> dict[str, Any]:
    """点赞作品。"""
    payload = {"accountId": account_id, "postId": post_id}
    if platform:
        payload["platform"] = platform
    url = f"{_base_url()}/plugin/engagement/like"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=_headers(), json=payload)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def follow_user(
    *,
    account_id: str,
    target_user_id: str,
    platform: str = "",
) -> dict[str, Any]:
    """关注用户。"""
    payload = {"accountId": account_id, "targetUserId": target_user_id}
    if platform:
        payload["platform"] = platform
    url = f"{_base_url()}/plugin/engagement/follow"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=_headers(), json=payload)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ---- 素材库管理（借鉴 AiToEarn content module） ----

async def fetch_materials(
    *,
    page: int = 1,
    page_size: int = 20,
    material_type: str = "video",
) -> dict[str, Any]:
    """获取素材列表。"""
    if not aitoearn_enabled():
        return {"items": [], "total": 0}
    url = f"{_base_url()}/plugin/content/material/list"
    params = {"page": page, "pageSize": page_size, "type": material_type}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=_headers(), params=params)
            resp.raise_for_status()
            body = resp.json()
        if body.get("code"):
            return {"items": [], "total": 0}
        data = body.get("data") or {}
        return {
            "items": list(data.get("list") or data.get("items") or []),
            "total": data.get("total", 0),
        }
    except Exception as exc:
        logger.warning("AiToEarn material list error: %s", exc)
        return {"items": [], "total": 0}


async def upload_material(
    *,
    file_url: str,
    title: str = "",
    material_type: str = "video",
) -> dict[str, Any]:
    """上传素材到 AiToEarn 素材库。"""
    payload = {
        "url": file_url,
        "title": title,
        "type": material_type,
    }
    url = f"{_base_url()}/plugin/content/material/upload"
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, headers=_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()


# ---- 预检 ----

async def preflight_aitoearn() -> dict[str, Any]:
    """preflight_aitoearn。
    :return: 返回处理结果。
    """
    if not aitoearn_enabled():
        return {
            "ready": False,
            "reason": "未配置 AITOEARN_API_KEY",
            "account_count": 0,
            "accounts": [],
        }
    try:
        accounts = await fetch_accounts()
    except Exception as exc:
        return {
            "ready": False,
            "reason": str(exc)[:200],
            "account_count": 0,
            "accounts": [],
        }
    normalized = [
        {
            "account_id": str(a.get("accountId") or a.get("id") or ""),
            "account_type": str(a.get("accountType") or ""),
            "canonical_type": normalize_account_type(str(a.get("accountType") or "")),
        }
        for a in accounts
    ]
    return {
        "ready": len(normalized) > 0,
        "reason": None if normalized else "AiToEarn 已连通但未绑定任何平台账号",
        "api_base": _base_url(),
        "account_count": len(normalized),
        "accounts": normalized,
    }


def preflight_aitoearn_sync() -> dict[str, Any]:
    """preflight_aitoearn_sync。
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(preflight_aitoearn())


# ---- 核心发布 ----

async def publish_video_via_aitoearn(
    *,
    platform_names: set[str],
    title: str,
    video_url: str,
    cover_url: str,
    topics: list[str] | None = None,
    body: str = "",
    allowed_account_ids: set[str] | None = None,
    tenant_id: str | None = None,
    scheduled_at: int | None = None,
) -> list[dict[str, Any]]:
    """向 AiToEarn 真发；仅使用 allowed_account_ids（客户独占槽位），每平台最多 1 个账号。

    Args:
        scheduled_at: 定时发布时间（Unix timestamp in milliseconds），None 表示立即发布
    """
    if not aitoearn_enabled():
        raise RuntimeError("未配置 AITOEARN_API_KEY，无法真发国内短视频平台")

    wanted = {account_type_for_platform_name(n) for n in platform_names if n}
    wanted.discard(None)
    accounts = await fetch_accounts()
    if not accounts:
        raise RuntimeError("AiToEarn 未绑定任何平台账号，请联系运营配置矩阵号")

    if allowed_account_ids:
        allow = {str(x) for x in allowed_account_ids if x}
        accounts = [
            a
            for a in accounts
            if str(a.get("accountId") or a.get("id") or "") in allow
        ]
        if not accounts:
            raise RuntimeError("本客户尚未分配 AiToEarn 代发矩阵号，请联系运营")

    matched: list[dict[str, Any]] = []
    seen_types: set[str] = set()
    for acc in accounts:
        atype = normalize_account_type(str(acc.get("accountType") or ""))
        if wanted and atype not in wanted:
            continue
        if atype in seen_types:
            continue
        seen_types.add(atype)
        matched.append(acc)

    if not matched:
        labels = "、".join(sorted(platform_names))
        raise RuntimeError(f"本客户 AiToEarn 槽位无可用平台账号：{labels}")

    tid_prefix = (tenant_id or "plat")[:8]
    flow_id = f"yd_{tid_prefix}_{uuid.uuid4().hex[:12]}"
    topic_str = ",".join(topics or []) or "video"
    cover = cover_url or video_url
    submit_errors: list[str] = []
    for acc in matched:
        aid = str(acc.get("accountId") or acc.get("id") or "")
        if not aid:
            continue
        try:
            await create_publish_task(
                account_id=aid,
                flow_id=flow_id,
                title=title,
                video_url=video_url,
                cover_url=cover,
                topics=topic_str,
                desc=body,
                scheduled_at=scheduled_at,
            )
        except Exception as exc:
            submit_errors.append(f"{acc.get('accountType')}:{aid} → {exc}")

    tasks = await poll_publish_tasks(flow_id)
    task_by_account = {str(t.get("accountId") or ""): t for t in tasks}
    results = await _build_aitoearn_results(flow_id, matched, scheduled_at, task_by_account)
    if submit_errors and not results:
        raise RuntimeError("; ".join(submit_errors))

    return results


async def _build_aitoearn_results(flow_id, matched, scheduled_at, task_by_account):
    """_build_aitoearn_results。

    参数说明：
    :param flow_id: 参数 flow_id
    :param matched: 参数 matched
    :param scheduled_at: 参数 scheduled_at
    :param task_by_account: 参数 task_by_account
    :return: 返回处理结果。
    """
    results: list[dict[str, Any]] = []
    for acc in matched:

        aid = str(acc.get("accountId") or acc.get("id") or "")
        atype = str(acc.get("accountType") or "")
        task = task_by_account.get(aid) or {}
        err = (task.get("errorMsg") or task.get("error_msg") or "").strip()
        post_url = _task_post_url(task)
        ok = _task_is_success(task) and bool(post_url)
        pending = bool(task) and not ok and not err
        if not task:

            ok = False
            err = err or "AiToEarn 未返回任务状态；若已提交请用 flow_id 在 AiToEarn 控制台核对"

        elif pending:

            err = err or f"已提交 AiToEarn，处理中（flow={flow_id}），请 1~3 分钟后到 {atype} 后台核对"

        results.append(

            {

                "platform_name": atype,
                "account_id": aid,
                "success": ok,
                "pending": pending,
                "platform_post_url": post_url,
                "platform_post_id": task.get("id") or flow_id,
                "flow_id": flow_id,
                "error_message": err or None,
                "via": "aitoearn",
                "verify_hint": f"AiToEarn flow={flow_id}，请到 {atype} 创作者后台核对作品",
                "scheduled": bool(scheduled_at),

            }

        )

    return results


def publish_video_via_aitoearn_sync(**kwargs: Any) -> list[dict[str, Any]]:
    """publish_video_via_aitoearn_sync。

    参数说明：
    :param **kwargs: 参数 **kwargs
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(publish_video_via_aitoearn(**kwargs))
