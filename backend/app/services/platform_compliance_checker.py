# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""多平台发帖合规预检 —— §3 缺口补齐。

各社媒平台对字数/话题标签/图片数/外链有硬边界，超了会被截断、拒收或降权。
发布前按目标平台校验，给出违规项 + 修正建议。纯规则，可离线单测。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

# ── 平台规格 ──────────────────────────────────────────────────────
@dataclass(frozen=True)
class PlatformLimits:
    platform: str
    max_chars: int
    max_hashtags: int = 30
    max_images: int = 0          # 0 = 不限/不适用
    allow_external_links: bool = True
    max_video_sec: int = 0       # 0 = 不限

PLATFORM_LIMITS: dict[str, PlatformLimits] = {
    "weibo": PlatformLimits("weibo", 2000, 10, 9, True, 0),
    "xiaohongshu": PlatformLimits("xiaohongshu", 1000, 20, 9, False, 0),  # 禁外链
    "linkedin": PlatformLimits("linkedin", 3000, 5, 0, True, 0),
    "twitter": PlatformLimits("twitter", 280, 5, 4, True, 0),
    "facebook": PlatformLimits("facebook", 63206, 30, 0, True, 0),
    "instagram_caption": PlatformLimits("instagram_caption", 2200, 30, 0, False, 0),
    "youtube_title": PlatformLimits("youtube_title", 100, 0, 0, True, 0),
    "youtube_description": PlatformLimits("youtube_description", 5000, 5, 0, True, 0),
    "douyin": PlatformLimits("douyin", 30000, 5, 0, False, 0),
}


@dataclass
class ComplianceCheck:
    valid: bool
    platform: str
    violations: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)
    char_count: int = 0
    hashtag_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["message"] = "发布合规" if self.valid else f"{self.platform} 合规违例 {len(self.violations)} 项"
        return d


_HASHTAG_RE = re.compile(r"#\S+", re.UNICODE)
_HTTP_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def _count_hashtags(text: str) -> int:
    return len(_HASHTAG_RE.findall(text or ""))


def _count_external_links(text: str) -> int:
    return len(_HTTP_RE.findall(text or ""))


def validate_post_content(
    content: dict[str, Any],
    platform: str,
) -> ComplianceCheck:
    """校验一条发帖内容是否符合平台边界。

    :param content: {"text":..., "image_count":..., "title":...}
    :param platform: PLATFORM_LIMITS 里的平台键
    """
    limits = PLATFORM_LIMITS.get(platform)
    text = str(content.get("text") or "")
    title = str(content.get("title") or "")
    image_count = int(content.get("image_count") or 0)

    if limits is None:
        return ComplianceCheck(
            valid=True, platform=platform,
            violations=[], suggestions=[f"未配置 {platform} 规格，按宽松处理"],
            char_count=len(text),
        )

    violations: list[str] = []
    suggestions: list[str] = []

    # 字数（标题型平台用 title，其余用 text）
    body = title if platform in ("youtube_title",) else text
    char_count = len(body)
    if char_count > limits.max_chars:
        overflow = char_count - limits.max_chars
        violations.append(f"字数超限：{char_count} > {limits.max_chars}（多 {overflow} 字）")
        suggestions.append(f"精简到 {limits.max_chars} 字以内，或去掉 {overflow} 字")

    # 话题标签
    tags = _count_hashtags(text + " " + title)
    if tags > limits.max_hashtags:
        violations.append(f"话题标签过多：{tags} > {limits.max_hashtags}")
        suggestions.append(f"删除 {tags - limits.max_hashtags} 个话题标签")

    # 图片数
    if image_count > limits.max_images and limits.max_images > 0:
        violations.append(f"图片数超限：{image_count} > {limits.max_images}")
        suggestions.append(f"最多 {limits.max_images} 张图，去掉 {image_count - limits.max_images} 张")

    # 外链
    if not limits.allow_external_links and _count_external_links(text) > 0:
        violations.append(f"{platform} 禁止正文外链")
        suggestions.append("把链接移到评论区或主页，避免被限流")

    return ComplianceCheck(
        valid=not violations,
        platform=platform,
        violations=violations,
        suggestions=suggestions,
        char_count=char_count,
        hashtag_count=tags,
    )


def list_platform_limits() -> list[dict[str, Any]]:
    return [
        {
            "platform": p.platform,
            "max_chars": p.max_chars,
            "max_hashtags": p.max_hashtags,
            "max_images": p.max_images,
            "allow_external_links": p.allow_external_links,
        }
        for p in PLATFORM_LIMITS.values()
    ]
