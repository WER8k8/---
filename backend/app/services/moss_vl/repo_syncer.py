# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""MOSS-VL 官方开源仓库自动化同步与环境检测工具。"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MossRepoSyncer:
    """官方仓库同步与物理整仓挂载器。"""

    OFFICIAL_REPO_URL = "https://github.com/OpenMOSS/MOSS-VL.git"

    def __init__(self, target_dir: str | Path | None = None):
        if target_dir:
            self.target_dir = Path(target_dir)
        else:
            # 兼容多种执行根目录路径
            cand = Path(__file__).resolve().parent.parent.parent.parent / "external" / "MOSS-VL"
            if cand.is_dir():
                self.target_dir = cand
            else:
                self.target_dir = Path.cwd() / "external" / "MOSS-VL"

    def check_git_installed(self) -> bool:
        return shutil.which("git") is not None

    def is_repo_present(self) -> bool:
        """检查官方整仓是否已经在本地就绪。"""
        if not self.target_dir.is_dir():
            return False
        # 必须包含官方核心脚本
        has_inference = (self.target_dir / "inference" / "run_inference.py").is_file()
        has_realtime = (self.target_dir / "realtime_inference" / "run_online_inference.py").is_file()
        return has_inference and has_realtime

    def ensure_repo_in_sys_path(self) -> list[str]:
        """将官方整仓及其核心代码目录注入 Python sys.path。"""
        paths_to_add = [
            str(self.target_dir),
            str(self.target_dir / "inference"),
            str(self.target_dir / "realtime_inference"),
            str(self.target_dir / "sglang" / "python"),
        ]
        added = []
        for p in paths_to_add:
            if os.path.exists(p) and p not in sys.path:
                sys.path.insert(0, p)
                added.append(p)
        return added

    def get_repo_inspection_report(self) -> dict[str, Any]:
        """对本地拉取的官方完整仓库做全景扫描与健康报告。"""
        exists = self.target_dir.is_dir()
        if not exists:
            return {
                "installed": False,
                "target_dir": str(self.target_dir),
                "msg": "未在本地检测到 MOSS-VL 官方整仓",
            }

        core_subdirs = ["inference", "realtime_inference", "finetune", "quant", "sglang"]
        subdir_status = {}
        for sd in core_subdirs:
            subdir_status[sd] = (self.target_dir / sd).is_dir()

        all_files = list(self.target_dir.rglob("*"))
        py_files = [f for f in all_files if f.suffix == ".py"]

        return {
            "installed": True,
            "target_dir": str(self.target_dir),
            "official_repo_url": self.OFFICIAL_REPO_URL,
            "core_subdirectories": subdir_status,
            "total_items_count": len(all_files),
            "python_source_files_count": len(py_files),
            "has_offline_inference_script": (self.target_dir / "inference" / "run_inference.py").is_file(),
            "has_online_realtime_script": (self.target_dir / "realtime_inference" / "run_online_inference.py").is_file(),
            "has_requirements_txt": (self.target_dir / "requirements.txt").is_file(),
            "sys_path_injected": any(str(self.target_dir) in p for p in sys.path),
        }

    def clone_or_pull_official_repo(self) -> dict[str, Any]:
        """拉取或同步官方仓库。"""
        if self.is_repo_present():
            return {
                "success": True,
                "action": "already_installed",
                "msg": "MOSS-VL 官方整仓已完整存在于本地",
                "target_dir": str(self.target_dir),
            }

        self.target_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            cmd = ["git", "clone", "--depth", "1", self.OFFICIAL_REPO_URL, str(self.target_dir)]
            subprocess.run(cmd, check=True, capture_output=True, timeout=180)
            return {
                "success": True,
                "action": "git clone",
                "msg": "成功拉取官方全套开源仓库源码",
                "target_dir": str(self.target_dir),
            }
        except Exception as e:
            return {
                "success": False,
                "action": "git clone",
                "msg": f"克隆超时或失败: {e}",
                "target_dir": str(self.target_dir),
            }
