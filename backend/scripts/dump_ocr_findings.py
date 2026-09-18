# -*- coding: utf-8 -*-
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
rep = json.loads((ROOT / "docs/opencode-review-report.json").read_text(encoding="utf-8"))

print("TOTAL", rep["findings_total"], "files", rep["files_scanned"])
print("SEV", rep["by_severity"])
print("\n==== BLOCKING DETAIL ====")
for f in rep["findings"]:
    if f["severity"] != "blocking":
        continue
    print(f"{f['file']}:{f['line']} [{f['rule']}] {f['message']}")
    if f.get("evidence"):
        print("   ", f["evidence"][:180])

print("\n==== PRIORITY MAJOR (silent-except sample in critical paths) ====")
maj = [f for f in rep["findings"] if f["severity"]=="major" and f.get("priority") and f["rule"]=="silent-except"]
print("count", len(maj))
for f in maj[:25]:
    print(f"{f['file']}:{f['line']} {f['evidence'][:100] if f.get('evidence') else ''}")

print("\n==== SQL FSTRING ALL ====")
for f in rep["findings"]:
    if f["rule"]=="security-sql-fstring":
        print(f"{f['file']}:{f['line']} {f['evidence'][:160]}")

print("\n==== HARD LOCKS / CONSISTENCY ====")
for f in rep["findings"]:
    if f["rule"] in ("LOGIN-LOCK-01","DESIGN-TOKEN-LOCK-01","route-duplicate","api-missing-backend","env-cwd-trap","resource-open","security-eval","security-shell","security-md5"):
        print(f"[{f['rule']}] {f['file']}:{f['line']} {f['message']} | {f.get('evidence','')[:120]}")
