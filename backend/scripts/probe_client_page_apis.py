# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
FILES = [
    "frontend/admin/src/views/client/foreign-trade-team.vue",
    "frontend/admin/src/views/client/chuhaiji-app.vue",
    "frontend/admin/src/views/client/aitoearn-engage.vue",
    "frontend/admin/src/views/client/templates-explore.vue",
    "frontend/admin/src/views/client/trade-tools.vue",
    "frontend/admin/src/views/client/site-editor-lab.vue",
]
PAT = re.compile(
    r"(api/v1/[^\s\"'`)]+|from\s+['\"]@/api[^'\"]*['\"]|request\(|axios\.|fetch\(|/acquisition|/products|/content|/publish|/annex)",
    re.I,
)

report = []
for rel in FILES:
    p = ROOT / rel
    item = {"file": rel, "exists": p.exists(), "hits": [], "api_paths": [], "imports": []}
    if not p.exists():
        report.append(item)
        continue
    text = p.read_text(encoding="utf-8", errors="ignore")
    for i, line in enumerate(text.splitlines(), 1):
        if PAT.search(line):
            item["hits"].append({"line": i, "text": line.strip()[:200]})
        for m in re.finditer(r"api/v1/([a-zA-Z0-9_/\-\{\}]+)", line):
            item["api_paths"].append(m.group(0))
        for m in re.finditer(r"from\s+['\"](@/api[^'\"]+)['\"]", line):
            item["imports"].append(m.group(1))
    item["api_paths"] = sorted(set(item["api_paths"]))
    item["imports"] = sorted(set(item["imports"]))
    report.append(item)

out = ROOT / "docs" / "probe_client_pages_api.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
for item in report:
    print("====", item["file"], "exists", item["exists"], "hits", len(item["hits"]))
    print("  imports", item["imports"])
    print("  api_paths", item["api_paths"][:30])
    for h in item["hits"][:15]:
        print(f"  L{h['line']}: {h['text'][:160]}")
print("written", out)
