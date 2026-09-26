# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""全站状态判定契约（SSOT）— 禁止各页面自写裸 status。

任何健康/集成/配置类接口必须返回：
  { "level": ok|warn|bad|info|skip, "label": 中文短标签, "hint": 大白话说明 }

前端只负责上色，不负责发明语义。
"""

from __future__ import annotations

from typing import Any, Iterable

LEVELS = ("ok", "warn", "bad", "info", "skip")

LEVEL_LABEL = {
    "ok": "正常",
    "warn": "需关注",
    "bad": "异常",
    "info": "可选/未启用",
    "skip": "跳过",
}

LEVEL_COLOR = {
    "ok": "success",
    "warn": "warning",
    "bad": "error",
    "info": "default",
    "skip": "default",
}


def check(
    level: str,
    label: str | None = None,
    hint: str = "",
    *,
    value: Any = None,
    **extra: Any,
) -> dict[str, Any]:
    lv = level if level in LEVELS else "info"
    out: dict[str, Any] = {
        "level": lv,
        "label": label or LEVEL_LABEL.get(lv, lv),
        "hint": hint or LEVEL_LABEL.get(lv, ""),
    }
    if value is not None:
        out["value"] = value
    out.update(extra)
    return out


def ok(label: str | None = None, hint: str = "", **kw: Any) -> dict[str, Any]:
    return check("ok", label, hint, **kw)


def warn(label: str | None = None, hint: str = "", **kw: Any) -> dict[str, Any]:
    return check("warn", label, hint, **kw)


def bad(label: str | None = None, hint: str = "", **kw: Any) -> dict[str, Any]:
    return check("bad", label, hint, **kw)


def info(label: str | None = None, hint: str = "", **kw: Any) -> dict[str, Any]:
    return check("info", label, hint, **kw)


def overall_from_checks(checks: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """聚合多项 check → 总判定。"""
    items = [c for c in checks if isinstance(c, dict)]
    levels = [c.get("level", "info") for c in items]
    if "bad" in levels:
        return check(
            "bad",
            "有阻断项",
            "存在红色项，请优先处理服务不可达或路由未挂载。",
        )
    if "warn" in levels:
        return check(
            "warn",
            "需关注",
            "存在黄色项，功能可能不完整，建议尽快补齐配置。",
        )
    if all(l == "info" for l in levels) and levels:
        return check(
            "info",
            "主路径可用",
            "主路径健康；可选旁路未启用，不影响主功能。",
        )
    return check(
        "ok",
        "主路径可用",
        "检查项均正常。",
    )


def sidecar_check(item: dict[str, Any] | None) -> dict[str, Any]:
    """旁路 sidecar 探针结果 → 标准 check。"""
    item = item or {}
    healthy = item.get("healthy")
    configured = bool(item.get("configured"))
    detail = str(item.get("detail") or "")
    probe = item.get("probe") or item.get("id") or "sidecar"

    if healthy is True and configured:
        return ok(hint=f"{probe} 旁路已配置且探活通过。" + (f"（{detail}）" if detail else ""), value=item)
    if healthy is False and configured:
        return bad(
            hint=f"{probe} 已配置但探活失败。" + (f"（{detail}）" if detail else "") + " 请检查进程/端口/依赖服务。",
            value=item,
        )
    if healthy is False and not configured:
        return info(
            hint=f"{probe} 未配置（可选旁路）。不影响主路径；需要该能力时再填环境变量/启动 sidecar。",
            value=item,
        )
    if healthy is None:
        return warn(hint=f"{probe} 探测超时或未返回。可能是启动中，或探针超时过短。", value=item)
    return info(hint=f"{probe} 状态未知，请点刷新或查看日志。", value=item)
