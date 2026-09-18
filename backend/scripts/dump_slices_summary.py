# -*- coding: utf-8 -*-
import json
from pathlib import Path

p = json.load(open(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix\docs\code_probe_slices.json", encoding="utf-8"))
pg = p["slice_pg"]
print("NONEMPTY_TABLES")
for d in pg.get("nonempty_top", []):
    print(f"  {d['table']}: {d['rows']}")
print("EMPTY_COUNT", pg.get("empty_count"))
print("PUBLIC", pg.get("pg_public_tables"))
print("MODEL_NOT_IN_PG", pg.get("in_models_not_in_pg"))
print("PG_NOT_IN_MODEL_COUNT", len(pg.get("in_pg_not_in_models") or []))
print("PG_NOT_IN_MODEL_SAMPLE", (pg.get("in_pg_not_in_models") or [])[:25])
print("CAPS")
for e in p["slice_executors"]["executors"]:
    names = ",".join(c["name"] for c in e["capabilities"])
    print(f"{e['executor']}|{e['capability_count']}|{names}")
print("BIZ_BIND", p["slice_executors"].get("biz_bot_module_binding_counts"))
print("ACQ", p["slice_acquisition"]["count"], p["slice_acquisition"]["router_prefix"])
