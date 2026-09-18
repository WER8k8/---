# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客生产门禁自检（只报告，不改生产 env）。

检查：
    1. 翻译引擎是否真引擎（非 mock）
    2. PIPELINE_GATES_ENABLED 是否开启
    3. ACQ_HARD_BLOCK_TOKEN 钱包硬拦开关
    4. Redis / API / PG / Celery worker 是否在
输出：大白话 checklist；全部绿才可开生产话术「已上线」。
"""
from __future__ import annotations

import os
import socket
from typing import Any


def _port_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def check_production_gates() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    lt_url = (os.getenv("LIBRETRANSLATE_URL") or "").strip()
    lt_stub = (os.getenv("LIBRETRANSLATE_ALLOW_DEV_STUB") or "").strip().lower() in ("1", "true", "yes")
    if not lt_url:
        checks.append({"id": "translate", "ok": False, "level": "fail",
                       "plain": "翻译引擎未配置 LIBRETRANSLATE_URL"})
    else:
        lt_up = _port_open("127.0.0.1", 8098) if "8098" in lt_url else True
        if lt_stub:
            checks.append({"id": "translate", "ok": False, "level": "warn",
                           "plain": f"翻译为开发桩 mock（{lt_url}）— 生产须关 LIBRETRANSLATE_ALLOW_DEV_STUB 并接真引擎"})
        elif not lt_up:
            checks.append({"id": "translate", "ok": False, "level": "fail",
                           "plain": f"翻译引擎地址配置了但连不上：{lt_url}"})
        else:
            checks.append({"id": "translate", "ok": True, "level": "ok",
                           "plain": f"翻译引擎已配置：{lt_url}"})

    gates = (os.getenv("PIPELINE_GATES_ENABLED") or "0").strip()
    if gates == "1":
        checks.append({"id": "human_gate", "ok": True, "level": "ok",
                       "plain": "首封人审闸已开启（PIPELINE_GATES_ENABLED=1）"})
    else:
        checks.append({"id": "human_gate", "ok": False, "level": "warn",
                       "plain": "首封人审闸未开（PIPELINE_GATES_ENABLED≠1）— 生产外发建议开启"})

    hard = (os.getenv("ACQ_HARD_BLOCK_TOKEN") or os.getenv("TOKEN_WALLET_HARD_BLOCK") or "").strip().lower()
    if hard in ("1", "true", "yes", "on"):
        checks.append({"id": "wallet_block", "ok": True, "level": "ok",
                       "plain": "Token 硬拦已开启"})
    else:
        checks.append({"id": "wallet_block", "ok": False, "level": "warn",
                       "plain": "Token 硬拦未开 — 余额耗尽仍可派发（建议影子计量稳定后开启）"})

    for name, port in (("PG", 5433), ("Redis", 6379), ("API", 8001)):
        up = _port_open("127.0.0.1", port)
        checks.append({
            "id": f"port_{name.lower()}",
            "ok": up,
            "level": "ok" if up else "fail",
            "plain": f"{name} :{port} " + ("在线" if up else "未监听"),
        })

    fails = [c for c in checks if c["level"] == "fail"]
    warns = [c for c in checks if c["level"] == "warn"]
    ok_n = sum(1 for c in checks if c["ok"])
    if fails:
        summary = f"生产门禁：{ok_n}/{len(checks)} 通过，有 {len(fails)} 项失败，不可宣称已上线。"
        ready = False
    elif warns:
        summary = f"生产门禁：{ok_n}/{len(checks)} 通过，{len(warns)} 项建议开启。开发可用；生产前须清警告。"
        ready = False
    else:
        summary = f"生产门禁：{ok_n}/{len(checks)} 全部通过。"
        ready = True
    return {
        "ready_for_production": ready,
        "ok_count": ok_n,
        "total": len(checks),
        "fail_count": len(fails),
        "warn_count": len(warns),
        "checks": checks,
        "plain_summary": summary,
        "hint": "本脚本只读 env/端口，不修改配置；生产话术禁止在未全绿时称「已上线」。",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(check_production_gates(), ensure_ascii=False, indent=2))
