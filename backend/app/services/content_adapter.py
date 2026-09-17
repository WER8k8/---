# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""内容多平台适配服务。

将原始内容按目标平台的字数限制、图片比例、标签数等规格自动适配。
纯计算，无外部依赖。
"""
from __future__ import annotations

import re
from typing import Any

PLATFORM_SPECS: dict[str, dict[str, Any]] = {
    "linkedin": {"text_limit": 3000, "image_ratio": "1.91:1", "hashtags": 5},
    "facebook": {"text_limit": 63206, "image_ratio": "1:1", "hashtags": 3},
    "instagram": {"text_limit": 2200, "image_ratio": "1:1", "hashtags": 30},
    "twitter": {"text_limit": 280, "image_ratio": "16:9", "hashtags": 3},
    "tiktok": {"text_limit": 2200, "image_ratio": "9:16", "hashtags": 5},
}

_HASHTAG_RE = re.compile(r"#\w+")


def _extract_hashtags(text: str, limit: int) -> list[str]:
    return _HASHTAG_RE.findall(text)[:limit]


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


class ContentAdapter:
    """内容多平台适配器。"""

    def adapt(self, content: str, platform: str) -> dict:
        """适配内容到指定平台。

        返回: {"text": str, "platform": str, "adapted": bool, "truncated": bool,
               "hashtags": list[str], "image_ratio": str}
        """
        spec = PLATFORM_SPECS.get(platform)
        if not spec:
            return {"text": content, "platform": platform, "adapted": False,
                    "truncated": False, "hashtags": [], "image_ratio": "",
                    "error": f"未知平台 {platform!r}，支持: {sorted(PLATFORM_SPECS)}"}

        text_limit = spec["text_limit"]
        truncated = len(content) > text_limit
        text = _truncate(content, text_limit)
        hashtags = _extract_hashtags(content, spec["hashtags"])

        return {
            "text": text,
            "platform": platform,
            "adapted": True,
            "truncated": truncated,
            "hashtags": hashtags,
            "image_ratio": spec["image_ratio"],
        }

    def adapt_batch(self, content: str, platforms: list[str] | None = None) -> list[dict]:
        """批量适配到所有或指定平台。"""
        targets = platforms or list(PLATFORM_SPECS)
        return [self.adapt(content, p) for p in targets]
