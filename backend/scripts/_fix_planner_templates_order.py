# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix\backend\app\services\hermes\planner_service.py")
text = p.read_text(encoding="utf-8")
start = text.find("# 意图关键词 → 构建器（按序匹配；具体意图优先于泛词）")
end = text.find("def _fulfillment_graph")
print("start", start, "end", end)
if start < 0 or end < 0 or start >= end:
    raise SystemExit("markers not found")
block = text[start:end]
rest = text[:start] + text[end:]
marker = "def _minimal_graph"
idx = rest.find(marker)
print("idx minimal", idx)
if idx < 0:
    raise SystemExit("minimal not found")
new = rest[:idx] + block + "\n\n" + rest[idx:]
p.write_text(new, encoding="utf-8")
print("ok templates", new.count("_TEMPLATES:"))
# sanity import check order
import ast
ast.parse(new)
print("syntax ok")
