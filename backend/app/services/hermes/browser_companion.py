"""浏览器伴侣插件 — 本地 Chrome/Edge 扩展，不进服务端执行。"""

from __future__ import annotations

from typing import Any

from app.services.hermes.registry import get_plugin, list_plugins


def _companion_meta(plugin: dict[str, Any]) -> dict[str, Any] | None:
    """_companion_meta。

    参数说明：
    :param plugin: 参数 plugin
    :return: 返回处理结果。
    """
    internal = plugin.get("internal") or {}
    if str(internal.get("kind") or "") != "browser_companion":
        return None
    return dict(plugin.get("public", {}).get("companion") or {})


def is_browser_companion(plugin_id: str) -> bool:
    """is_browser_companion。

    参数说明：
    :param plugin_id: 参数 plugin_id
    :return: 返回处理结果。
    """
    spec = get_plugin(plugin_id)
    return spec is not None and _companion_meta(spec) is not None


def list_browser_companions(*, content_type: str | None = None) -> list[dict[str, Any]]:
    """列出可推荐给客户的本地浏览器扩展。"""
    out: list[dict[str, Any]] = []
    for p in list_plugins(visibility="public"):
        companion = _companion_meta(p)
        if not companion:
            continue
        types = companion.get("content_types") or []
        if content_type and content_type not in types:
            continue
        pub = p.get("public") or {}
        install = companion.get("install") or {}
        out.append(
            {
                "id": p.get("id"),
                "name": pub.get("name"),
                "tagline": pub.get("tagline"),
                "description": pub.get("description"),
                "category": pub.get("category"),
                "content_types": types,
                "platforms": companion.get("platforms") or [],
                "install_kind": "local_browser",
                "platform_exclusive": bool(companion.get("platform_exclusive")),
                "launch_route": companion.get("launch_route"),
                "install": install,
                "disclaimer": companion.get("disclaimer"),
                "recommended_for": companion.get("recommended_for"),
                "marketplace_path": "/client/plugin-market?category=浏览器伴侣",
            }
        )
    return out


def browser_companion_hint(*, content_type: str = "video") -> dict[str, Any]:
    """视频/图文分发弹窗：仅引导从优丁工作台唤起伴侣，不提供独立外站用法。"""
    items = list_browser_companions(content_type=content_type)
    launch_route = "/admin/ai-center/browser-companion"
    return {
        "title": "优丁专属 · 浏览器伴侣（可选）",
        "message": (
            "伴侣插件仅能从优丁工作台打开并带入本平台视频/图文，不能脱离优丁单独使用。"
            "云端 Worker 真发仍是主路径；伴侣用于 Worker 未就绪时在本地草稿箱微调。"
        ),
        "platform_exclusive": True,
        "launch_route": launch_route,
        "items": items,
        "marketplace_path": "/client/plugin-market?category=浏览器伴侣",
    }
