# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
data = json.loads((ROOT / "docs/ocr-scan-critical.json").read_text(encoding="utf-8"))

print("STATUS", data.get("status"))
print("LLM", data.get("llm"))
print("SUMMARY", json.dumps(data.get("summary"), ensure_ascii=False, indent=2))
print("WARNINGS", data.get("warnings"))
print("\n==== PROJECT SUMMARY ====")
print(data.get("project_summary") or "")

comments = data.get("comments") or []
print("\nCOMMENTS", len(comments))
if comments:
    print("keys", comments[0].keys())

# normalize
rows = []
for c in comments:
    if not isinstance(c, dict):
        continue
    rows.append(
        {
            "file": c.get("file") or c.get("path") or c.get("filePath") or "",
            "line": c.get("line") or c.get("start_line") or c.get("lineNumber") or "",
            "severity": (c.get("severity") or c.get("level") or c.get("priority") or "").lower(),
            "rule": c.get("rule") or c.get("category") or c.get("type") or "",
            "title": (c.get("title") or c.get("summary") or "")[:120],
            "body": (c.get("body") or c.get("comment") or c.get("message") or c.get("description") or "").replace("\n", " ")[:400],
        }
    )

by_sev = Counter(r["severity"] or "unknown" for r in rows)
by_file = Counter(r["file"] for r in rows)
print("BY_SEV", dict(by_sev))
print("BY_FILE top")
for f, n in by_file.most_common(20):
    print(f"  {n:2} {f}")

print("\n==== ALL COMMENTS ====")
for r in sorted(rows, key=lambda x: (x["file"], str(x["line"]))):
    print(f"[{r['severity'] or '?'}] {r['file']}:{r['line']} {r['rule']}")
    print(f"    {r['title']}")
    if r["body"]:
        print(f"    {r['body'][:280]}")

out = {
    "tool": "OpenCodeReview alibaba/open-code-review v1.12.5",
    "mode": "ocr scan LLM",
    "provider": data.get("llm"),
    "status": data.get("status"),
    "summary": data.get("summary"),
    "warnings": data.get("warnings"),
    "project_summary": data.get("project_summary"),
    "session_id": data.get("session_id"),
    "comment_count": len(rows),
    "by_severity": dict(by_sev),
    "comments": rows,
    "raw_comment_keys_sample": list(comments[0].keys()) if comments else [],
}
(ROOT / "docs" / "ocr-scan-critical-parsed.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nwritten docs/ocr-scan-critical-parsed.json")
