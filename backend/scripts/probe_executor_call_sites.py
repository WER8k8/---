# -*- coding: utf-8 -*-
"""Slice B: for each registered executor, find real call-site evidence in source."""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
APP = ROOT / "backend" / "app"
EXEC_DIR = APP / "services/hermes/executors"
sys.path.insert(0, str(ROOT / "backend"))

CALL_MARKERS = {
    "http": re.compile(r"httpx\.|requests\.|urllib\.request|aiohttp", re.I),
    "db": re.compile(r"SessionLocal|context\.db|db\.query|db\.execute|select\(|insert\(|text\(", re.I),
    "service_import": re.compile(r"from app\.services\.|import app\.services\."),
    "model_import": re.compile(r"from app\.models\.|import app\.models\."),
    "env_config": re.compile(r"os\.getenv|os\.environ"),
}


def analyze_executor(path: Path) -> dict:
    src = path.read_text(encoding="utf-8", errors="ignore")
    # executor name
    m = re.search(r"return\s+[\"']([a-z0-9_]+)[\"']", src)
    name = m.group(1) if m else path.stem.replace("_executor", "")

    caps = re.findall(r"[\"']([a-z0-9_]+\.[a-z0-9_]+|[a-z0-9_]+)[\"']\s*:\s*\{", src)
    # better: capability keys in _CAPS dict
    cap_block = re.search(r"_CAPS\s*=\s*\{(.*?)\n\}", src, re.S)
    cap_names = re.findall(r"[\"']([^\"']+)[\"']\s*:\s*\{", cap_block.group(1)) if cap_block else []

    evidence = {
        "http_client": bool(CALL_MARKERS["http"].search(src)),
        "db_session": bool(CALL_MARKERS["db"].search(src)),
        "imports_app_services": bool(CALL_MARKERS["service_import"].search(src)),
        "imports_models": bool(CALL_MARKERS["model_import"].search(src)),
        "reads_env": bool(CALL_MARKERS["env_config"].search(src)),
    }

    # service modules referenced
    services = sorted(set(re.findall(r"from app\.services\.([a-zA-Z0-9_\.]+)", src)))
    models = sorted(set(re.findall(r"from app\.models\.([a-zA-Z0-9_]+)", src)))

    # classify depth
    if evidence["http_client"] and (evidence["db_session"] or evidence["imports_app_services"]):
        depth = "C_http+local"
    elif evidence["http_client"]:
        depth = "C_http"
    elif evidence["db_session"] or evidence["imports_models"]:
        depth = "B_db_or_model"
    elif evidence["imports_app_services"]:
        depth = "B_service_call"
    elif "module_matrix" in name or name == "module_matrix":
        depth = "B_route_import"
    else:
        # still may call services via lazy import inside functions
        if "from app.services" in src or "importlib" in src:
            depth = "B_service_call"
        else:
            depth = "A_declaration_only"

    # lazy imports count
    lazy = len(re.findall(r"from app\.services\.", src))
    return {
        "executor": name,
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "capability_count": len(cap_names),
        "capabilities": cap_names,
        "evidence": evidence,
        "service_refs": services[:20],
        "model_refs": models[:15],
        "service_import_lines": lazy,
        "depth": depth,
        "loc": src.count("\n") + 1,
    }


def main() -> None:
    items = []
    for p in sorted(EXEC_DIR.glob("*_executor.py")):
        items.append(analyze_executor(p))
    from app.services.hermes.executors import ExecutorRegistry

    registered = set(ExecutorRegistry.list_executors())
    for it in items:
        it["registered"] = it["executor"] in registered

    by_depth: dict[str, list[str]] = {}
    for it in items:
        by_depth.setdefault(it["depth"], []).append(it["executor"])

    report = {
        "count": len(items),
        "registered_count": len(registered),
        "by_depth": {k: sorted(v) for k, v in sorted(by_depth.items())},
        "by_depth_counts": {k: len(v) for k, v in sorted(by_depth.items())},
        "executors": items,
        "legend": {
            "A_declaration_only": "源码几乎无 app.services/models/http/db 痕迹（可能极薄或纯注册）",
            "B_service_call": "有 app.services 调用/懒加载（本地业务逻辑）",
            "B_db_or_model": "有 Session/db.query 或 models import",
            "B_route_import": "module_matrix：真 import 路由模块",
            "C_http": "有 httpx/requests 等外呼",
            "C_http+local": "外呼 + 本地 DB/service",
        },
    }
    out = ROOT / "docs" / "probe_executor_call_sites.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("COUNT", report["count"], "registered", report["registered_count"])
    print("BY_DEPTH", report["by_depth_counts"])
    for d, names in report["by_depth"].items():
        print(d, ":", ", ".join(names))
    print("--- detail ---")
    for it in items:
        ev = it["evidence"]
        flags = "".join(
            [
                "H" if ev["http_client"] else "-",
                "D" if ev["db_session"] else "-",
                "S" if ev["imports_app_services"] else "-",
                "M" if ev["imports_models"] else "-",
                "E" if ev["reads_env"] else "-",
            ]
        )
        print(f"{it['executor']:16} {it['depth']:16} {flags} loc={it['loc']:4} caps={it['capability_count']} svc={len(it['service_refs'])}")
    print("written", out)


if __name__ == "__main__":
    main()
