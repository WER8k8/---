"""VID-11：多平台标题/描述长度适配。"""

from __future__ import annotations

PLATFORM_LIMITS: dict[str, int] = {
    "douyin": 55,
    "抖音": 55,
    "bilibili": 80,
    "b站": 80,
    "xiaohongshu": 20,
    "小红书": 20,
    "weixin": 30,
    "视频号": 30,
    "baijiahao": 40,
    "百家号": 40,
    "default": 60,
}


def adapt_title(title: str, platform: str | None = None) -> str:
    """实现 adapt标题 的功能。
    
    :param title: 参数 title（类型: str）
    :param platform: 参数 platform（类型: str | None）
    :return: 返回 str 结果
    """
    raw = (title or "").strip() or "视频"
    key = (platform or "default").strip().lower()
    limit = PLATFORM_LIMITS.get(key, PLATFORM_LIMITS["default"])
    if len(raw) <= limit:
        return raw
    if limit <= 20:
        return raw[: limit - 1] + "…"
    return raw[: limit - 3] + "..."
