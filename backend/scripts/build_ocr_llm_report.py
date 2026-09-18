# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
raw = json.loads((ROOT / "docs/ocr-scan-critical.json").read_text(encoding="utf-8"))
comments = raw.get("comments") or []

rows = []
for c in comments:
    rows.append(
        {
            "path": c.get("path") or "",
            "start_line": c.get("start_line"),
            "end_line": c.get("end_line"),
            "category": c.get("category") or "",
            "severity": (c.get("severity") or "").lower(),
            "content": (c.get("content") or "").strip(),
            "existing_code": (c.get("existing_code") or "")[:300],
        }
    )

by_sev = Counter(r["severity"] for r in rows)
by_cat = Counter(r["category"] for r in rows)
by_file = Counter(r["path"] for r in rows)

md = [
    "# OpenCodeReview LLM 扫描报告（关键路径）",
    "",
    f"- 工具：alibaba/open-code-review **v1.12.5**",
    f"- Provider：`{raw.get('llm')}`",
    f"- 状态：`{raw.get('status')}`（部分子任务因 token 预算/超时未完成）",
    f"- 文件评审数：**{raw.get('summary',{}).get('files_reviewed')}**",
    f"- 评论数：**{len(rows)}**（high {by_sev.get('high',0)} / medium {by_sev.get('medium',0)} / low {by_sev.get('low',0)}）",
    f"- Token：{raw.get('summary',{}).get('total_tokens')} · 耗时 {raw.get('summary',{}).get('elapsed')} · budget_exceeded={raw.get('summary',{}).get('budget_exceeded')}",
    f"- Session：`{raw.get('session_id')}`",
    "",
    "## 项目摘要（OCR 输出原文）",
    "",
    raw.get("project_summary") or "(empty)",
    "",
    "## 警告 / 未完成文件",
    "",
]
for w in raw.get("warnings") or []:
    md.append(f"- `{w.get('file')}` · {w.get('type')} · {w.get('message')}")

md += ["", "## 按文件统计", "", "| 文件 | 评论数 |", "|------|------:|"]
for f, n in by_file.most_common():
    md.append(f"| `{f}` | {n} |")

md += ["", "## 按类别统计", "", "| 类别 | 数量 |", "|------|-----:|"]
for k, n in by_cat.most_common():
    md.append(f"| {k} | {n} |")

md += ["", "## High 级评论（全文）", ""]
for r in sorted([x for x in rows if x["severity"] == "high"], key=lambda x: (x["path"], x["start_line"] or 0)):
    md.append(f"### `{r['path']}`:{r['start_line']}-{r['end_line']} · {r['category']}")
    md.append("")
    md.append(r["content"] or "(no content)")
    if r["existing_code"]:
        md.append("")
        md.append("```python")
        md.append(r["existing_code"])
        md.append("```")
    md.append("")

md += ["", "## Medium 级评论（标题级）", ""]
for r in sorted([x for x in rows if x["severity"] == "medium"], key=lambda x: (x["path"], x["start_line"] or 0)):
    first = (r["content"] or "").splitlines()[0] if r["content"] else ""
    md.append(f"- `{r['path']}`:{r['start_line']} · **{r['category']}** · {first[:160]}")

md += ["", "## Low 级评论（标题级）", ""]
for r in sorted([x for x in rows if x["severity"] == "low"], key=lambda x: (x["path"], x["start_line"] or 0)):
    first = (r["content"] or "").splitlines()[0] if r["content"] else ""
    md.append(f"- `{r['path']}`:{r['start_line']} · **{r['category']}** · {first[:160]}")

md += [
    "",
    "## 与静态检测交叉",
    "",
    "- OCR LLM **独立确认**：`/ops/reconcile` 重复路由、大量 except 吞异常、acquisition 异步阻塞、billing_explain 诚实性问题。",
    "- OCR 新发现（静态规则难覆盖）：BuyerMasterStore 竞态与全局状态、`rebind_engine` 丢 RoutingSession、P95 计算错误、`HERMES_SITE_PATROL_HTTP_SELF_URL` 硬编码、敏感端点缺限流、`card.sample` 空引用风险。",
    "",
    "## 机读",
    "",
    "- 原始：`docs/ocr-scan-critical.json`",
    "- 解析：`docs/ocr-scan-critical-parsed.json`",
    "",
]
(ROOT / "docs" / "ocr-scan-critical-report.md").write_text("\n".join(md), encoding="utf-8")

parsed = {
    **{k: raw.get(k) for k in ("status", "llm", "summary", "warnings", "project_summary", "session_id")},
    "comment_count": len(rows),
    "by_severity": dict(by_sev),
    "by_category": dict(by_cat),
    "by_file": dict(by_file),
    "comments": rows,
}
(ROOT / "docs" / "ocr-scan-critical-parsed.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
print("by_sev", dict(by_sev))
print("by_cat", dict(by_cat))
print("high files:")
for r in rows:
    if r["severity"] == "high":
        print(f"  {r['path']}:{r['start_line']} {r['category']}")
print("written docs/ocr-scan-critical-report.md")
print("sample high content len", len(next(r['content'] for r in rows if r['severity']=='high')))
