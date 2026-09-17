# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""发布后验真 — 无 platform URL/ID 一律不算成功。"""

from __future__ import annotations

import re
from typing import Any

_URL_PATTERNS = (
    re.compile(r"https?://(?:www\.)?bilibili\.com/video/(BV[\w]+)", re.I),
    re.compile(r"https?://(?:www\.)?douyin\.com/video/\d+", re.I),
    re.compile(r"https?://v\.douyin\.com/[\w/-]+", re.I),
    re.compile(r"https?://(?:www\.)?kuaishou\.com/short-video/[\w-]+", re.I),
    re.compile(r"https?://(?:www\.)?xiaohongshu\.com/explore/[\w]+", re.I),
    re.compile(r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+", re.I),
    re.compile(r"https?://youtu\.be/[\w-]+", re.I),
    re.compile(r"https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+", re.I),
)

_BVID_PATTERN = re.compile(r"\b(BV[\w]{10})\b")


def extract_post_url_from_text(text: str) -> str:
    """实现 提取postURLfrom文本 的功能。
    
    :param text: 参数 text（类型: str）
    :return: 返回 str 结果
    """
    for pat in _URL_PATTERNS:
        m = pat.search(text or "")
        if m:
            return m.group(0)
    return ""


def extract_bvid_from_text(text: str) -> str:
    """实现 提取bvidfrom文本 的功能。
    
    :param text: 参数 text（类型: str）
    :return: 返回 str 结果
    """
    m = _BVID_PATTERN.search(text or "")
    return m.group(1) if m else ""


def verify_publish_outcome(outcome: dict[str, Any]) -> dict[str, Any]:
    """强制验真：success 仅当存在可核对的作品 URL 或平台原生 ID。"""
    result = dict(outcome)
    url = (result.get("platform_post_url") or "").strip()
    post_id = (result.get("platform_post_id") or "").strip()
    if not url and result.get("raw_output"):
        url = extract_post_url_from_text(str(result.get("raw_output")))
        if url:
            result["platform_post_url"] = url

    if not post_id and not url and result.get("raw_output"):
        bvid = extract_bvid_from_text(str(result.get("raw_output")))
        if bvid:
            post_id = bvid
            result["platform_post_id"] = bvid
            if not url:
                result["platform_post_url"] = f"https://www.bilibili.com/video/{bvid}"

    has_evidence = bool(url or post_id)
    if result.get("pending"):
        result["success"] = False
        result["verified"] = False
        if not result.get("error_message"):
            result["error_message"] = "任务处理中，尚未获得可验证作品链接"
        return result

    if has_evidence:
        result["success"] = True
        result["verified"] = True
        result["error_message"] = None
    else:
        result["success"] = False
        result["verified"] = False
        err = (result.get("error_message") or "").strip()
        result["error_message"] = err or "发布未返回可验证作品链接，请到平台创作者后台核对"

    return result
