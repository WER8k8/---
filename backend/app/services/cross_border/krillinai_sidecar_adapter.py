# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""KrillinAI sidecar/CLI 适配器 — 仅在上游就绪时调用，禁止假成功。"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.cross_border.opensource_localization_registry import is_krillinai_configured


def krillinai_probe() -> dict[str, Any]:
    """探测 KrillinAI CLI 或 sidecar 是否可达（不执行翻译）。"""
    if not is_krillinai_configured():
        return {
            "ok": False,
            "error_code": "KRILLINAI_NOT_CONFIGURED",
            "hint": "设置 KRILLINAI_CLI_PATH 或 KRILLINAI_SERVICE_URL 后重试",
        }

    cli = (settings.KRILLINAI_CLI_PATH or "").strip()
    if cli:
        path = Path(cli)
        exe = str(path) if path.is_file() else cli
        try:
            proc = subprocess.run(
                [exe, "--help"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if proc.returncode == 0 or "Krillin" in (proc.stdout or proc.stderr or ""):
                return {"ok": True, "backend": "krillinai_cli", "path": exe}
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {
                "ok": False,
                "error_code": "KRILLINAI_CLI_UNREACHABLE",
                "hint": str(exc),
            }

    url = (settings.KRILLINAI_SERVICE_URL or "").strip()
    if url:
        return {
            "ok": True,
            "backend": "krillinai_http",
            "service_url": url,
            "hint": "HTTP 健康检查待 MS-H-02 实现",
        }

    return {
        "ok": False,
        "error_code": "KRILLINAI_NOT_CONFIGURED",
        "hint": "未找到可用的 KrillinAI 路径或服务",
    }


def run_krillinai_localization(
    *,
    video_path: Path,
    target_lang: str = "en",
    source_lang: str = "zh",
) -> dict[str, Any]:
    """
    调用 KrillinAI 全链路（MS-H-02 完整实现前返回明确未就绪）。
    有 CLI 时仅做 probe；实际 pipeline 需 sidecar 编排，避免半成品假成功。
    """
    probe = krillinai_probe()
    if not probe.get("ok"):
        return {**probe, "ok": False}

    return {
        "ok": False,
        "error_code": "KRILLINAI_PIPELINE_NOT_WIRED",
        "hint": (
            "KrillinAI 已探测就绪，完整 pipeline 编排见 MS-H-02；"
            "当前请继续使用自研标准轨或配置 Linly-Dubbing sidecar"
        ),
        "probe": probe,
        "video_path": str(video_path),
        "target_lang": target_lang,
        "source_lang": source_lang,
    }
