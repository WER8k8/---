# -*- coding: utf-8 -*-
"""Merge all OCR LLM scan JSON files into one comprehensive report."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
DOCS = ROOT / "docs"

FILES = [
    "ocr-scan-critical-full.json",
    "ocr-scan-batch2.json",
    "ocr-scan-batch3.json",
    "ocr-scan-batch4.json",
    "ocr-scan-batch5-payment.json",
    "ocr-scan-batch6-acq-rest.json",
    "ocr-scan-batch7-acq-route.json",
]

all_comments: list[dict] = []
runs: list[dict] = []
warnings_all: list[dict] = []
summaries: list[str] = []

for name in FILES:
    p = DOCS / name
    if not p.exists():
        runs.append({"file": name, "exists": False})
        continue
    d = json.loads(p.read_text(encoding="utf-8"))
    cs = d.get("comments") or []
    runs.append(
        {
            "file": name,
            "exists": True,
            "status": d.get("status"),
            "llm": d.get("llm"),
            "summary": d.get("summary"),
            "comment_count": len(cs),
            "warnings": d.get("warnings") or [],
            "session_id": d.get("session_id"),
        }
    )
    warnings_all.extend([{**w, "scan": name} for w in (d.get("warnings") or [])])
    if d.get("project_summary"):
        summaries.append(f"## 来自 {name}\n\n{d['project_summary']}")
    for c in cs:
        all_comments.append({**c, "_scan": name})

# dedupe by path + start_line + content prefix
seen = set()
unique = []
for c in all_comments:
    key = (
        c.get("path") or "",
        c.get("start_line"),
        (c.get("content") or "")[:80],
        c.get("category") or "",
        (c.get("severity") or "").lower(),
    )
    if key in seen:
        continue
    seen.add(key)
    unique.append(c)

sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "": 4}
unique.sort(key=lambda c: (sev_order.get((c.get("severity") or "").lower(), 9), c.get("path") or "", c.get("start_line") or 0))

by_sev = Counter((c.get("severity") or "unknown").lower() for c in unique)
by_cat = Counter(c.get("category") or "unknown" for c in unique)
by_file = Counter(c.get("path") or "?" for c in unique)

# remaining incomplete
incomplete = []
for r in runs:
    for w in r.get("warnings") or []:
        incomplete.append(f"{w.get('file')} · {w.get('type')} · {w.get('message')}")

merged = {
    "tool": "OpenCodeReview alibaba/open-code-review v1.12.5",
    "mode": "ocr scan LLM multi-batch",
    "provider_used": sorted({(r.get("llm") or {}).get("provider", "") for r in runs if r.get("llm")} - {""}),
    "models_used": sorted({(r.get("llm") or {}).get("model", "") for r in runs if r.get("llm")} - {""}),
    "runs": runs,
    "comment_count_raw": len(all_comments),
    "comment_count_unique": len(unique),
    "by_severity": dict(by_sev),
    "by_category": dict(by_cat),
    "by_file": dict(by_file.most_common()),
    "incomplete_warnings": incomplete,
    "project_summaries": summaries,
    "comments": [
        {
            "path": c.get("path"),
            "start_line": c.get("start_line"),
            "end_line": c.get("end_line"),
            "category": c.get("category"),
            "severity": (c.get("severity") or "").lower(),
            "content": (c.get("content") or "").strip(),
            "existing_code": (c.get("existing_code") or "")[:400],
            "scan": c.get("_scan"),
        }
        for c in unique
    ],
}

(DOCS / "ocr-scan-merged.json").write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

# markdown
md = [
    "# OpenCodeReview LLM 全量合并报告",
    "",
    "> 多批次扫描合并 · 去重后意见 · 密钥未入库",
    "",
    f"- 工具：alibaba/open-code-review **v1.12.5**",
    f"- Provider/Model：{merged['provider_used']} / {merged['models_used']}",
    f"- 批次数：{len([r for r in runs if r.get('exists')])}",
    f"- 意见：原始 {len(all_comments)} → **去重 {len(unique)}**",
    f"- 级别：**critical {by_sev.get('critical',0)}** · high {by_sev.get('high',0)} · medium {by_sev.get('medium',0)} · low {by_sev.get('low',0)} · unknown {by_sev.get('unknown',0)}",
    "",
    "## 各批次运行",
    "",
    "| 文件 | 状态 | 评审文件数 | 意见数 | token | 超预算 |",
    "|------|------|----------:|------:|------:|:------:|",
]
for r in runs:
    if not r.get("exists"):
        md.append(f"| `{r['file']}` | 缺失 | - | - | - | - |")
        continue
    s = r.get("summary") or {}
    md.append(
        f"| `{r['file']}` | {r.get('status')} | {s.get('files_reviewed')} | {r.get('comment_count')} | {s.get('total_tokens')} | {s.get('budget_exceeded')} |"
    )

md += ["", "## 按文件（去重后 Top）", "", "| 文件 | 意见数 |", "|------|------:|"]
for f, n in by_file.most_common(30):
    md.append(f"| `{f}` | {n} |")

md += ["", "## 按类别", "", "| 类别 | 数量 |", "|------|-----:|"]
for k, n in by_cat.most_common():
    md.append(f"| {k} | {n} |")

md += ["", "## 仍未完整扫完（诚实）", ""]
if incomplete:
    for x in incomplete:
        md.append(f"- {x}")
else:
    md.append("- （本合并范围内警告已列出；个别超大文件可能仍有子任务超时）")

md += ["", "## Critical 全文", ""]
for c in unique:
    if (c.get("severity") or "").lower() != "critical":
        continue
    md.append(f"### `{c.get('path')}`:{c.get('start_line')}-{c.get('end_line')} · {c.get('category')}")
    md.append("")
    md.append((c.get("content") or "").strip() or "(empty)")
    if c.get("existing_code"):
        md += ["", "```python", c["existing_code"], "```"]
    md.append("")

md += ["", "## High 全文", ""]
for c in unique:
    if (c.get("severity") or "").lower() != "high":
        continue
    md.append(f"### `{c.get('path')}`:{c.get('start_line')}-{c.get('end_line')} · {c.get('category')}")
    md.append("")
    md.append((c.get("content") or "").strip() or "(empty)")
    if c.get("existing_code"):
        md += ["", "```python", c["existing_code"], "```"]
    md.append("")

md += ["", "## Medium / Low 索引", ""]
for sev in ("medium", "low"):
    md.append(f"### {sev}")
    md.append("")
    for c in unique:
        if (c.get("severity") or "").lower() != sev:
            continue
        first = (c.get("content") or "").splitlines()[0] if c.get("content") else ""
        md.append(f"- `{c.get('path')}`:{c.get('start_line')} · **{c.get('category')}** · {first[:150]}")
    md.append("")

if summaries:
    md += ["", "## OCR 项目级摘要（各批原文）", ""]
    md.extend(summaries)

md += [
    "",
    "## 机读",
    "",
    "- 合并：`docs/ocr-scan-merged.json`",
    "- 各批：`docs/ocr-scan-critical-full.json` 等",
    "",
]
(DOCS / "ocr-scan-merged-report.md").write_text("\n".join(md), encoding="utf-8")

print("unique", len(unique), "from", len(all_comments))
print("by_sev", dict(by_sev))
print("critical", by_sev.get("critical", 0), "high", by_sev.get("high", 0))
print("top files", by_file.most_common(12))
print("incomplete", len(incomplete))
print("written docs/ocr-scan-merged.json / ocr-scan-merged-report.md")
# list critical+high one-liners
print("\nCRITICAL+HIGH:")
for c in unique:
    if (c.get("severity") or "").lower() in ("critical", "high"):
        first = (c.get("content") or "").splitlines()[0] if c.get("content") else ""
        print(f"  [{c.get('severity')}] {c.get('path')}:{c.get('start_line')} {c.get('category')} | {first[:100]}")
