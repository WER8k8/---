#!/usr/bin/env python3
"""SEC-04：pip audit + npm audit 归档到 docs/security-audit-latest.md"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "security-audit-latest.md"


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _pip_audit(backend: Path) -> tuple[int, str]:
    """pip audit（优先 pip-audit 包，兼容旧 pip 无 audit 子命令）。"""
    for cmd in (
        [sys.executable, "-m", "pip_audit"],
        [sys.executable, "-m", "pip", "audit"],
    ):
        code, out = _run(cmd, backend)
        if "unknown command" not in out.lower() and "No module named" not in out:
            return code, out
    return (
        1,
        "未安装 pip-audit。请执行: pip install pip-audit\n"
        "然后: python -m pip_audit",
    )


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# 依赖安全审计（自动生成）",
        "",
        f"> 生成时间：{ts}",
        "",
        "## Python（backend）",
        "",
        "```text",
    ]
    code, pip_out = _pip_audit(ROOT / "backend")
    lines.append(pip_out.strip() or "(no output)")
    lines.append("```")
    lines.append("")
    lines.append("## Node（frontend/admin）")
    lines.append("")
    admin = ROOT / "frontend" / "admin"
    if (admin / "package-lock.json").exists():
        try:
            code_npm, npm_out = _run(["npm", "audit", "--json"], admin)
            lines.append("```json")
            lines.append(npm_out.strip() or "{}")
            lines.append("```")
        except FileNotFoundError:
            lines.append("_未找到 npm 命令，跳过 npm audit_")
            code_npm = -1
    else:
        lines.append("_无 package-lock.json，跳过 npm audit_")
        code_npm = 0
    lines.extend(
        [
            "",
            "## 说明",
            "",
            f"- pip audit 退出码：{code}",
            "- 高危项需评估升级；生产部署前与 preflight 一并执行",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
