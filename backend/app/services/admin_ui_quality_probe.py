# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""超管 UI 质量探针 — 供 Hermes 巡站 / 手动体检共用。

检查（只读、可离线）：
1. UI emoji（产品禁止）
2. font-weight 600/700（马卡龙仅 400/500）
3. 状态页是否缺少好坏说明（hint/判定）
4. a-descriptions 真缺 column（误匹配 -item 已排除）
5. 菜单重复 path（叶子项）
6. 菜单 path 是否能在 router 文本中命中（弱检查）
7. 过时叙事（缺适配器/外挂桥）

返回 status_judgement 契约：level/label/hint
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from app.services.status_judgement import bad, check, ok, warn

_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U0001F900-\U0001F9FF\U00002600-\U000027BF\U0000FE0F\U00002B50\U00002728\U0000274C\U00002705\U000026A0]"
)
_BOLD_RE = re.compile(r"font-weight:\s*(600|700)")
_DESC_TAG_RE = re.compile(r"<a-descriptions(?=[\s>])([^>]*)>")
_DESC_ITEM_RE = re.compile(r"<a-descriptions-item\b")
_STALE_RE = re.compile(r"ready_for_adapter|缺少正式适配器|外挂桥缺失")
_PATH_RE = re.compile(r"path:\s*'([^']+)'")
_HINT_RE = re.compile(r"hint|判定|status-hint-note|LevelTag|status_judgement")


def _admin_src() -> Path | None:
    # 1) 环境变量
    env = os.environ.get("YOUDING_ADMIN_SRC")
    if env and Path(env).is_dir():
        return Path(env)
    # 2) 相对本文件上溯 worktree frontend/admin/src
    here = Path(__file__).resolve()
    for p in here.parents:
        cand = p / "frontend" / "admin" / "src"
        if cand.is_dir():
            return cand
    return None


def _iter_files(root: Path, suffixes: tuple[str, ...]):
    skip = {"node_modules", "__pycache__", ".git", "dist"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for name in filenames:
            if name.endswith(suffixes):
                yield Path(dirpath) / name


def probe_admin_ui_quality() -> dict[str, Any]:
    """扫描超管前端源码，输出 UI 质量判定。"""
    root = _admin_src()
    if root is None:
        return {
            **warn(
                hint="未找到 frontend/admin/src，跳过 UI 质量扫描。可设置 YOUDING_ADMIN_SRC。"
            ),
            "id": "admin_ui_quality",
            "title": "超管 UI 质量",
            "checked": False,
        }

    findings: list[dict[str, Any]] = []
    emoji_files = 0
    bold_hits = 0
    missing_column = 0
    status_no_hint = 0
    stale_narrative = 0
    menu_dups = 0
    scanned_vue = 0

    vue_files = list(_iter_files(root, (".vue",)))
    style_files = list(_iter_files(root, (".scss", ".css", ".vue")))
    menu_files = list(root.glob("constants/*Menu*.ts"))

    for f in vue_files:
        scanned_vue += 1
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = str(f.relative_to(root)).replace("\\", "/")
        if _EMOJI_RE.search(text):
            emoji_files += 1
            findings.append({"type": "emoji", "file": rel})
        bold_hits += len(_BOLD_RE.findall(text))
        for tag in _DESC_TAG_RE.findall(text):
            if "column" not in tag:
                missing_column += 1
                findings.append({"type": "descriptions_no_column", "file": rel})
        if _STALE_RE.search(text):
            stale_narrative += 1
            findings.append({"type": "stale_narrative", "file": rel})
        # 状态页无说明：启发式
        if re.search(r"status_label|not_configured|集成|健康", text) and not _HINT_RE.search(text):
            status_no_hint += 1
            findings.append({"type": "status_no_hint", "file": rel})

    for f in style_files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        bold_hits += len(_BOLD_RE.findall(text))

    for f in menu_files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        paths = _PATH_RE.findall(text)
        seen: dict[str, int] = {}
        for p in paths:
            seen[p] = seen.get(p, 0) + 1
        # 叶子重复：同 path 出现 ≥3（父+子同 path 常见 2 次）
        for p, n in seen.items():
            if n >= 3:
                menu_dups += 1
                findings.append({"type": "menu_path_heavy_dup", "path": p, "count": n})
        if _EMOJI_RE.search(text):
            emoji_files += 1
            findings.append({"type": "emoji", "file": f.name})

    issues = emoji_files + (1 if bold_hits else 0) + missing_column + status_no_hint + stale_narrative + menu_dups

    summary = {
        "scanned_vue": scanned_vue,
        "emoji_files": emoji_files,
        "bold_hits": bold_hits,
        "descriptions_no_column": missing_column,
        "status_no_hint": status_no_hint,
        "stale_narrative": stale_narrative,
        "menu_path_heavy_dup": menu_dups,
        "findings_sample": findings[:20],
        "findings_total": len(findings),
    }

    if missing_column > 0 or stale_narrative > 0 or emoji_files > 5:
        base = bad(
            hint=(
                f"超管 UI 质量有阻断项：emoji 文件 {emoji_files}，"
                f"descriptions 缺 column {missing_column}，过时叙事 {stale_narrative}。"
                "请按 findings 清理；巡站不会自动改前端。"
            ),
            value=summary,
        )
    elif issues > 0:
        base = warn(
            hint=(
                f"超管 UI 质量需关注：emoji 文件 {emoji_files}，字重超标 {bold_hits}，"
                f"状态缺说明 {status_no_hint}，菜单重度重复 {menu_dups}。"
            ),
            value=summary,
        )
    else:
        base = ok(hint="超管 UI 质量扫描通过：无 emoji / 无过粗字重 / 无空列 / 无过时叙事。", value=summary)

    return {
        **base,
        "id": "admin_ui_quality",
        "title": "超管 UI 质量",
        "checked": True,
    }
