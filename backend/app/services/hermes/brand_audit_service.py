# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""COMP-02 品牌抽检：扫描租户/落地页可见文案是否泄露禁词。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

FORBIDDEN_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bDeerFlow\b", re.I), "DeerFlow"),
    (re.compile(r"\bUBrain\b", re.I), "UBrain"),
    (re.compile(r"\bAccioWork\b", re.I), "AccioWork"),
    (re.compile(r"\bAccio\b"), "Accio"),
    (re.compile(r"\bHermes\b", re.I), "Hermes"),
)

SKIP_PATH_PARTS: tuple[str, ...] = (
    "brand_guard",
    "brand_audit",
    "deerflow",
    "hermes/",
    "ubrain/",
    "test_",
    ".cursor",
    "node_modules",
    "deploy/docs",
    "docs/",
)

CUSTOMER_SCAN_ROOTS: tuple[str, ...] = (
    "frontend/admin/src/views/client",
    "frontend/admin/src/views/landing",
    "frontend/admin/src/views/tenants/site-editor.vue",
    "frontend/site",
)

SCAN_EXTENSIONS: frozenset[str] = frozenset({".vue", ".ts", ".tsx", ".js", ".html"})

# 代码行（非用户可见）跳过
_CODE_LINE_MARKERS: tuple[str, ...] = (
    "fetch(",
    "import ",
    "from '",
    'from "',
    "/api/",
    "api/v1",
    "const ",
    "let ",
    "function ",
    "await ",
    "//",
    "/*",
    "router.",
    "path:",
    "name:",
)


def _extract_vue_template(text: str) -> str:
    """_extract_vue_template。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    start = text.find("<template")
    if start < 0:
        return ""
    end = text.find("</template>", start)
    if end < 0:
        return ""
    return text[start:end]


def _line_likely_user_visible(line: str) -> bool:
    """_line_likely_user_visible。

    参数说明：
    :param line: 参数 line
    :return: 返回处理结果。
    """
    s = line.strip()
    if not s:
        return False
    lower = s.lower()
    for marker in _CODE_LINE_MARKERS:
        if marker in lower or marker in s:
            return False
    return True


def _iter_scan_lines(path: Path, text: str) -> list[tuple[int, str]]:
    """_iter_scan_lines。

    参数说明：
    :param path: 参数 path
    :param text: 参数 text
    :return: 返回处理结果。
    """
    if path.suffix == ".vue":
        block = _extract_vue_template(text)
        if not block:
            return []
        lines: list[tuple[int, str]] = []
        in_template = False
        for i, raw in enumerate(text.splitlines(), start=1):
            if "<template" in raw and not in_template:
                in_template = True
            if in_template:
                if _line_likely_user_visible(raw):
                    lines.append((i, raw))
            if in_template and "</template>" in raw:
                break
        return lines
    return [(i, ln) for i, ln in enumerate(text.splitlines(), start=1) if _line_likely_user_visible(ln)]


def _repo_root() -> Path:
    """_repo_root。
    :return: 返回处理结果。
    """
    return Path(__file__).resolve().parents[4]


def _should_scan(path: Path, repo_root: Path) -> bool:
    """_should_scan。

    参数说明：
    :param path: 参数 path
    :param repo_root: 参数 repo_root
    :return: 返回处理结果。
    """
    rel = str(path.relative_to(repo_root)).replace("\\", "/").lower()
    for part in SKIP_PATH_PARTS:
        if part.lower() in rel:
            return False
    for root in CUSTOMER_SCAN_ROOTS:
        r = root.lower().replace("\\", "/")
        if r.endswith(".vue") or r.endswith(".ts"):
            if rel == r:
                return True
        elif rel.startswith(r):
            return True
    return False


def audit_brand_leaks(
    repo_root: Path | None = None,
    max_findings: int = 50,
) -> dict[str, Any]:
    """audit_brand_leaks。

    参数说明：
    :param repo_root: 参数 repo_root
    :param max_findings: 参数 max_findings
    :return: 返回处理结果。
    """
    root = repo_root or _repo_root()
    violations: list[dict[str, Any]] = []
    scanned = 0
    for ext in SCAN_EXTENSIONS:
        for path in root.rglob(f"*{ext}"):
            if not _should_scan(path, root):
                continue
            scanned += 1
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel = str(path.relative_to(root)).replace("\\", "/")
            for line_no, line in _iter_scan_lines(path, text):
                for pattern, label in FORBIDDEN_PATTERNS:
                    if pattern.search(line):
                        violations.append(
                            {
                                "file": rel,
                                "line": line_no,
                                "term": label,
                                "excerpt": line.strip()[:120],
                            }
                        )
                        break
                if len(violations) >= max_findings:
                    break
            if len(violations) >= max_findings:
                break
        if len(violations) >= max_findings:
            break

    return {
        "ok": len(violations) == 0,
        "violations_count": len(violations),
        "violations": violations,
        "files_scanned": scanned,
        "scope": list(CUSTOMER_SCAN_ROOTS),
    }
