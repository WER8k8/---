# -*- coding: utf-8 -*-
"""OpenCodeReview host-agent detector.

Implements alibaba/open-code-review built-in Python review rules as static checks,
plus YouDing project hard locks. No LLM required (OCR CLI LLM endpoint unavailable).
Rules source: ocr rules check <file> (System built-in **/*.{py,pyi,ipynb})
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
SCAN_ROOTS = [
    ROOT / "backend/app",
    ROOT / "backend/scripts",
]
# prioritize business-critical
PRIORITY_SUBSTRINGS = (
    "hermes",
    "acquisition",
    "api/v1/routes",
    "payment",
    "auth",
    "core/config",
    "core/database",
    "adapters",
    "goodjob",
)

findings: list[dict[str, Any]] = []


def add(file: Path, line: int, rule: str, severity: str, msg: str, evidence: str = "") -> None:
    rel = str(file.relative_to(ROOT)).replace("\\", "/")
    findings.append(
        {
            "file": rel,
            "line": line,
            "rule": rule,
            "severity": severity,
            "message": msg,
            "evidence": evidence.strip()[:200],
            "priority": any(s in rel for s in PRIORITY_SUBSTRINGS),
        }
    )


def scan_py(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(text)
    except Exception:
        return
    lines = text.splitlines()

    # regex rules on source
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("#"):
            continue
        # mutable default
        if re.search(r"def\s+\w+\([^)]*=\s*(\[\]|\{\})", line):
            add(path, i, "mutable-default", "blocking", "可变默认参数 []/{}", line)
        # bare except
        if re.search(r"^\s*except\s*:\s*(#.*)?$", line):
            add(path, i, "bare-except", "blocking", "裸 except: 会吞掉一切异常", line)
        # silent except pass
        if re.search(r"except\s+[^:]+:\s*$", line) and i < len(lines) and re.match(r"^\s*pass\s*(#.*)?$", lines[i]):
            add(path, i, "silent-except", "major", "except 后直接 pass，错误被静默", f"{line} / {lines[i]}")
        # eval/exec
        if re.search(r"\b(eval|exec)\s*\(", line) and "ast." not in line:
            add(path, i, "security-eval", "blocking", "存在 eval/exec 调用", line)
        # shell=True
        if "shell=True" in line or "shell = True" in line:
            add(path, i, "security-shell", "blocking", "subprocess shell=True", line)
        # yaml.load unsafe
        if re.search(r"yaml\.load\s*\(", line) and "SafeLoader" not in line and "safe_load" not in line:
            add(path, i, "security-yaml", "blocking", "yaml.load 未使用 SafeLoader", line)
        # SQL f-string / concat
        if re.search(r"(execute|exec_driver_sql)\s*\(\s*f[\"']", line) or re.search(
            r"text\(\s*f[\"'].*(SELECT|INSERT|UPDATE|DELETE)", line, re.I
        ):
            add(path, i, "security-sql-fstring", "blocking", "SQL 使用 f-string 拼接风险", line)
        # secrets in logs
        if re.search(r"(api_key|password|secret|token)\s*[=:]\s*[\"'][^\"']{8,}[\"']", line, re.I):
            if "getenv" not in line and "placeholder" not in line.lower() and "example" not in line.lower():
                if re.search(r"(nvapi-|sk-|Bearer\s+\w{10,})", line) or re.search(
                    r"(api_key|password|secret)\s*=\s*[\"'][^\"'$\{]{12,}[\"']", line, re.I
                ):
                    add(path, i, "security-secret-literal", "blocking", "疑似密钥明文写在代码里", line)
        # md5 for security-ish
        if re.search(r"hashlib\.md5\s*\(", line):
            add(path, i, "security-md5", "major", "使用 MD5（安全场景不推荐）", line)
        # logging f-string hot path style
        if re.search(r"logger\.\w+\(\s*f[\"']", line):
            add(path, i, "perf-log-fstring", "minor", "logging 使用 f-string（禁用级别时仍格式化）", line)
        # TODO/FIXME debt markers in critical path
        if "PRIORITY" in "".join(PRIORITY_SUBSTRINGS) and re.search(r"\b(TODO|FIXME|XXX|HACK)\b", line):
            if any(p in str(path).replace("\\", "/") for p in PRIORITY_SUBSTRINGS):
                add(path, i, "debt-marker", "minor", "关键路径存在 TODO/FIXME", line)

    # AST rules
    for node in ast.walk(tree):
        # is comparison with literals (non-None)
        if isinstance(node, ast.Compare):
            for op, comparator in zip(node.ops, node.comparators):
                if isinstance(op, (ast.Is, ast.IsNot)):
                    if isinstance(comparator, ast.Constant) and comparator.value not in (None, True, False, Ellipsis):
                        if isinstance(comparator.value, (str, int, float, bytes, tuple)):
                            add(
                                path,
                                getattr(node, "lineno", 0),
                                "identity-literal",
                                "major",
                                f"使用 is/is not 与字面量比较: {comparator.value!r}",
                                "",
                            )
        # assert for runtime validation heuristics: assert in function with request-like names nearby
        if isinstance(node, ast.Assert):
            # skip doc-style asserts in tests
            if "/tests/" in str(path).replace("\\", "/"):
                continue
            add(path, node.lineno, "assert-runtime", "minor", "生产代码使用 assert（-O 会被剥离）", "")

        # open without with — heuristic Call open assigned not in with
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            parent_ok = False
            # coarse: if this line contains 'with ' it's fine
            ln = getattr(node, "lineno", 0)
            if ln and ln <= len(lines) and "with " in lines[ln - 1]:
                parent_ok = True
            if not parent_ok:
                # many are inside with on same/prev line; only flag if clearly bare assignment
                if ln and re.search(r"=\s*open\s*\(", lines[ln - 1]) and "with " not in lines[ln - 1]:
                    add(path, ln, "resource-open", "major", "open() 可能未用 with 管理", lines[ln - 1])


def project_hard_locks() -> None:
    # LOGIN lock
    client_login = ROOT / "frontend/admin/src/views/client/login.vue"
    if client_login.exists():
        add(client_login, 0, "LOGIN-LOCK-01", "blocking", "禁止存在的第二套登录页 client/login.vue")
    # mint color
    ui = ROOT / "frontend/admin/src/stores/uiPreferences.ts"
    if ui.exists():
        t = ui.read_text(encoding="utf-8", errors="ignore")
        if "PLATFORM_BRAND_DEFAULT = '#4a9b8c'" not in t and 'PLATFORM_BRAND_DEFAULT = "#4a9b8c"' not in t:
            add(ui, 0, "DESIGN-TOKEN-LOCK-01", "blocking", "平台主色不是薄荷 #4a9b8c")
        # hard-coded non-mint primary in tailwind
    tail = ROOT / "frontend/admin/tailwind.config.js"
    if tail.exists():
        t = tail.read_text(encoding="utf-8", errors="ignore")
        if "#4a9b8c" not in t:
            add(tail, 0, "DESIGN-TOKEN-LOCK-01", "blocking", "admin tailwind 未含薄荷主色")
    # acquisition duplicate route
    acq = ROOT / "backend/app/api/v1/routes/acquisition.py"
    if acq.exists():
        t = acq.read_text(encoding="utf-8", errors="ignore")
        if t.count('"/ops/reconcile"') + t.count("'/ops/reconcile'") >= 2:
            add(acq, 0, "route-duplicate", "major", "acquisition.py 中 /ops/reconcile 装饰器重复声明")
    # frontend dangling API
    engage = ROOT / "frontend/admin/src/views/client/aitoearn-engage.vue"
    if engage.exists():
        t = engage.read_text(encoding="utf-8", errors="ignore")
        if "douyin-comments" in t:
            routes = list((ROOT / "backend/app/api/v1/routes").glob("*.py"))
            hit = any("douyin" in p.read_text(encoding="utf-8", errors="ignore").lower() for p in routes)
            if not hit:
                add(engage, 0, "api-missing-backend", "major", "前端调用 /api/v1/client/douyin-comments/pull 但后端无 douyin 路由")
    # config cwd/db trap documentation as finding
    backend_env = ROOT / "backend/.env"
    if backend_env.exists():
        t = backend_env.read_text(encoding="utf-8", errors="ignore")
        if "postgresql" in t.lower():
            add(backend_env, 0, "env-cwd-trap", "major", "env 声明 PG，但脚本 cwd≠backend 时会落到 SQLite（运行时陷阱）")


def main() -> None:
    project_hard_locks()
    py_files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        py_files.extend(root.rglob("*.py"))
    # exclude venv-like
    py_files = [p for p in py_files if ".venv" not in str(p) and "__pycache__" not in str(p)]
    for p in py_files:
        scan_py(p)

    # stats
    by_rule: dict[str, int] = {}
    by_sev: dict[str, int] = {}
    for f in findings:
        by_rule[f["rule"]] = by_rule.get(f["rule"], 0) + 1
        by_sev[f["severity"]] = by_sev.get(f["severity"], 0) + 1
    priority = [f for f in findings if f.get("priority")]
    blocking = [f for f in findings if f["severity"] == "blocking"]

    report = {
        "tool": "OpenCodeReview (alibaba/open-code-review) host-agent mode",
        "ocr_version": "v1.12.5",
        "ocr_cli": "installed global @alibaba-group/open-code-review",
        "llm_status": "unavailable — NVIDIA integrate.api.nvidia.com returned 410 Gone; Ollama registry TLS timeout",
        "rules_source": "ocr rules check — System built-in **/*.{py,pyi,ipynb}",
        "scan_roots": [str(p.relative_to(ROOT)).replace("\\", "/") for p in SCAN_ROOTS],
        "files_scanned": len(py_files),
        "findings_total": len(findings),
        "by_severity": by_sev,
        "by_rule": dict(sorted(by_rule.items(), key=lambda x: -x[1])),
        "priority_findings_count": len(priority),
        "blocking_count": len(blocking),
        "ocr_preview_hermes_files": 119,
        "findings": findings,
        "note": "本报告 = OpenCodeReview 官方规则集 + CLI 范围/规则解析 + 宿主代理静态检测；非 OCR 内置 LLM 自动评审（端点不可用）。",
    }
    out = ROOT / "docs" / "opencode-review-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # markdown summary
    md = [
        "# OpenCodeReview 全面检测报告 · 优丁工作树",
        "",
        f"- 工具：`alibaba/open-code-review` CLI **v1.12.5**（`ocr` 已全局安装）",
        f"- 规则源：`ocr rules check` 内置 Python 规则（精确优先、安全/正确性 blocking）",
        f"- LLM：**不可用**（NVIDIA `410 Gone`；Ollama 模型拉取 TLS 超时）→ 采用 **Delegation/宿主代理** 模式",
        f"- 扫描：`backend/app` + `backend/scripts`，文件 **{len(py_files)}**",
        f"- 发现合计 **{len(findings)}**（blocking {by_sev.get('blocking',0)} / major {by_sev.get('major',0)} / minor {by_sev.get('minor',0)}）",
        f"- 关键路径命中 **{len(priority)}** 条",
        "",
        "## 按规则统计",
        "",
        "| 规则 | 数量 |",
        "|------|-----:|",
    ]
    for k, v in report["by_rule"].items():
        md.append(f"| `{k}` | {v} |")
    md += ["", "## Blocking（须优先处理）", ""]
    for f in blocking[:80]:
        md.append(f"- **{f['file']}:{f['line']}** · `{f['rule']}` · {f['message']}")
        if f.get("evidence"):
            md.append(f"  - `{f['evidence'][:160]}`")
    if len(blocking) > 80:
        md.append(f"- … 另有 {len(blocking)-80} 条，见 JSON")
    md += ["", "## 关键路径 Major（节选）", ""]
    maj_p = [f for f in findings if f["severity"] == "major" and f.get("priority")]
    for f in maj_p[:40]:
        md.append(f"- **{f['file']}:{f['line']}** · `{f['rule']}` · {f['message']}")
    md += [
        "",
        "## 项目硬锁/一致性",
        "",
    ]
    for f in findings:
        if f["rule"] in (
            "LOGIN-LOCK-01",
            "DESIGN-TOKEN-LOCK-01",
            "route-duplicate",
            "api-missing-backend",
            "env-cwd-trap",
        ):
            md.append(f"- **{f['rule']}** · {f['file']} · {f['message']}")
    md += [
        "",
        "## 如何复跑",
        "",
        "```powershell",
        "ocr --version",
        "ocr rules check backend/app/services/acquisition/payment_risk.py",
        "ocr scan --preview --repo . --path backend/app/services/hermes",
        "# LLM 可用后：",
        "ocr config set provider openai  # 或自定义",
        "ocr scan --path backend/app/services/acquisition --format json -o docs/ocr-scan.json",
        "```",
        "",
        "机读全量：`docs/opencode-review-report.json`",
    ]
    (ROOT / "docs" / "opencode-review-report.md").write_text("\n".join(md), encoding="utf-8")

    print(json.dumps({k: report[k] for k in ("files_scanned", "findings_total", "by_severity", "by_rule", "priority_findings_count", "blocking_count", "llm_status")}, ensure_ascii=False, indent=2))
    print("written", out)


if __name__ == "__main__":
    main()
