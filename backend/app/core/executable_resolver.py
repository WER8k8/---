# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Resolve CLI executables on Windows (uvicorn subprocess often lacks WinGet shim PATH)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def _winget_package_exe(localappdata: str, name: str) -> str | None:
    """WinGet 常装 symlink；Python 子进程解析失败时直接扫 Packages 实文件。"""
    packages = Path(localappdata) / "Microsoft" / "WinGet" / "Packages"
    if not packages.is_dir():
        return None
    exe_name = f"{name}.exe"
    patterns = (
        f"**/{exe_name}",
        f"**/bin/{exe_name}",
    )
    if name == "ffmpeg":
        patterns = (
            "Gyan.FFmpeg_*/ffmpeg-*/bin/ffmpeg.exe",
            "ffmpeg*/**/bin/ffmpeg.exe",
            *patterns,
        )
    hits: list[Path] = []
    for pattern in patterns:
        hits.extend(packages.glob(pattern))
    if not hits and name == "ffmpeg":
        hits = [
            p for p in packages.rglob("ffmpeg.exe")
            if p.is_file() and p.parent.name.lower() == "bin"
        ]
    for path in sorted(hits, key=lambda p: p.stat().st_mtime if p.is_file() else 0, reverse=True):
        if path.is_file() and path.stat().st_size > 0:
            return str(path)
    return None


def _probe_executable(path: str) -> bool:
    """Run `-version` instead of Path.is_file() — WinGet symlink targets may fail is_file()."""
    if not (path or "").strip():
        return False
    try:
        proc = subprocess.run(
            [path, "-version"],
            capture_output=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return proc.returncode == 0
    except Exception:
        try:
            return Path(path).resolve().is_file()
        except OSError:
            return False


def _read_winget_link_target(link: Path) -> str | None:
    """_read_winget_link_target。

    参数说明：
    :param link: 参数 link
    :return: 返回处理结果。
    """
    if not link.exists() and not link.is_symlink():
        return None
    try:
        raw = os.readlink(link)
        target = Path(raw)
        if not target.is_absolute():
            target = (link.parent / target).resolve()
        if _probe_executable(str(target)):
            return str(target)
    except OSError:
        pass
    try:
        resolved = link.resolve()
        if _probe_executable(str(resolved)):
            return str(resolved)
    except OSError:
        pass
    return None


def resolve_executable(name: str) -> str | None:
    """返回可执行文件的绝对路径，不存在则返回 None。"""
    env_key = f"{name.upper()}_PATH"
    env_path = (os.environ.get(env_key) or "").strip()
    if env_path:
        p = Path(env_path)
        try:
            resolved = p.resolve()
            if resolved.is_file():
                return str(resolved)
        except OSError:
            pass
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            pkg = _winget_package_exe(localappdata, name)
            if pkg:
                return pkg
        return env_path

    found = shutil.which(name)
    if found:
        return found
    localappdata = os.environ.get("LOCALAPPDATA", "")
    if not localappdata:
        return None
    winget_link = Path(localappdata) / "Microsoft" / "WinGet" / "Links" / f"{name}.exe"
    link_target = _read_winget_link_target(winget_link)
    if link_target:
        return link_target
    if winget_link.exists():
        try:
            resolved = winget_link.resolve()
            if resolved.is_file():
                return str(resolved)
        except OSError:
            pass
        pkg = _winget_package_exe(localappdata, name)
        if pkg:
            return pkg
        return str(winget_link)
    pkg = _winget_package_exe(localappdata, name)
    if pkg:
        return pkg
    return None


def is_executable_available(name: str) -> bool:
    """is_executable_available。

    参数说明：
    :param name: 参数 name
    :return: 返回处理结果。
    """
    path = resolve_executable(name)
    if not path:
        return False
    return _probe_executable(path)


def bootstrap_executable_env() -> None:
    """开发/Windows：uvicorn 子进程常缺 WinGet PATH，启动时补 FFMPEG_PATH 等。"""
    for exe in ("ffmpeg", "ffprobe"):
        env_key = f"{exe.upper()}_PATH"
        if (os.environ.get(env_key) or "").strip() and is_executable_available(exe):
            continue
        resolved = resolve_executable(exe)
        if resolved and _probe_executable(resolved):
            os.environ[env_key] = resolved
