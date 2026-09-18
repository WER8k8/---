# -*- coding: utf-8 -*-
"""Slice C: client admin routes → backend module / API path mapping (code-only)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
ADMIN_SRC = ROOT / "frontend/admin/src"
ROUTER = ADMIN_SRC / "router/index.ts"
ROUTES_DIR = ROOT / "backend/app/api/v1/routes"
API_TS_DIR = ADMIN_SRC / "api"


def parse_client_routes() -> list[dict]:
    text = ROUTER.read_text(encoding="utf-8", errors="ignore")
    # extract client children block roughly
    m = re.search(r"path:\s*['\"]/client['\"]", text)
    if not m:
        return []
    # find children array after this
    cm = re.search(r"children:\s*\[", text[m.start():])
    if not cm:
        return []
    start = m.start() + cm.end() - 1
    depth = 0
    end = start
    for j in range(start, len(text)):
        if text[j] == "[":
            depth += 1
        elif text[j] == "]":
            depth -= 1
            if depth == 0:
                end = j
                break
    block = text[start : end + 1]
    rows = []
    for rm in re.finditer(r"path:\s*['\"]([^'\"]+)['\"]", block):
        raw = rm.group(1)
        if raw == "" and rm.start() < 50:
            continue
        window = block[rm.start() : rm.start() + 420]
        title_m = re.search(r"title:\s*['\"]([^'\"]+)['\"]", window)
        comp_m = re.search(r"component:\s*\(\)\s*=>\s*import\(['\"]([^'\"]+)['\"]\)", window)
        name_m = re.search(r"name:\s*['\"]([^'\"]+)['\"]", window)
        full = raw if raw.startswith("/client") else f"/client/{raw}".replace("//", "/")
        if raw == "/client" or raw == "client":
            full = "/client"
        rows.append(
            {
                "path": full,
                "raw": raw,
                "title": title_m.group(1) if title_m else "",
                "name": name_m.group(1) if name_m else "",
                "component": comp_m.group(1) if comp_m else "",
            }
        )
    # unique by path keep first
    seen = set()
    out = []
    for r in rows:
        if r["path"] in seen:
            continue
        seen.add(r["path"])
        out.append(r)
    return out


# heuristic: frontend path segment → candidate backend route modules
PATH_TO_MODULES = [
    (r"acquisition|ops|prospect|outreach|inquir", ["acquisition", "inquiries", "crm_pipeline", "follow_up", "opportunity"]),
    (r"product", ["products", "product_commerce", "product_commercial", "product_faqs"]),
    (r"seo", ["seo_matrix", "seo_diagnosis", "rank_check"]),
    (r"content|article", ["content", "content_master", "knowledge"]),
    (r"publish|distribute|cross-platform", ["unified_publish", "publish_tasks", "cross_platform_dashboard"]),
    (r"video|media|image-space|file", ["media_factory", "moss_vl_clip_publish", "multimodal_studio", "files", "annex"]),
    (r"token|billing|invoice|plan", ["token_ledger", "wallet", "payment", "license"]),
    (r"inquir", ["inquiries", "inquiry_channels", "acquisition"]),
    (r"egress|ip", ["egress"]),
    (r"workspace|skill|assistant|copilot|ai-", ["skill_store", "ai_generate", "ai_config", "ai_templates", "ubrain"]),
    (r"email|campaign", ["email_campaigns", "email_queue", "email_tracking"]),
    (r"queue", ["inquiries", "publish_tasks", "acquisition"]),
    (r"geo", ["public_tenant_geo", "seo_matrix"]),
    (r"annex|trade-ai|goodjob", ["foreign_trade", "cross_border", "invoice_applications", "annex"]),
    (r"referral", ["referral"]),
    (r"settings", ["settings"]),
    (r"traffic|analytics", ["analytics", "metrics", "site_ai_generator"]),
    (r"onboarding|dashboard|today", ["onboarding", "system_health", "acquisition"]),
]


def match_modules(path: str, component: str) -> list[str]:
    hay = f"{path} {component}".lower()
    mods: list[str] = []
    for pat, candidates in PATH_TO_MODULES:
        if re.search(pat, hay):
            for c in candidates:
                if c not in mods:
                    mods.append(c)
    return mods


def backend_module_exists(name: str) -> bool:
    return (ROUTES_DIR / f"{name}.py").exists()


def scan_api_ts() -> dict[str, list[str]]:
    """frontend admin api/*.ts → referenced backend path fragments."""
    out: dict[str, list[str]] = {}
    if not API_TS_DIR.exists():
        return out
    for p in sorted(API_TS_DIR.rglob("*.ts")):
        t = p.read_text(encoding="utf-8", errors="ignore")
        paths = re.findall(r"[\"'`](/?api/v1/[^\"'`\s]+)", t)
        paths += re.findall(r"url:\s*[\"']([^\"']+)[\"']", t)
        out[str(p.relative_to(ROOT)).replace("\\", "/")] = sorted(set(paths))[:40]
    return out


def main() -> None:
    routes = parse_client_routes()
    mapped = []
    for r in routes:
        mods = match_modules(r["path"], r["component"] + " " + r["title"])
        existing = [m for m in mods if backend_module_exists(m)]
        missing = [m for m in mods if not backend_module_exists(m)]
        mapped.append({**r, "candidate_modules": mods, "modules_exist": existing, "modules_missing": missing})

    covered = sum(1 for m in mapped if m["modules_exist"])
    no_backend = [m for m in mapped if not m["modules_exist"]]

    # backend modules never hinted by client routes
    hinted = set()
    for m in mapped:
        hinted.update(m["modules_exist"])
        hinted.update(m["candidate_modules"])
    all_backend = sorted(p.stem for p in ROUTES_DIR.glob("*.py") if not p.name.startswith("__"))
    not_in_client_hints = sorted(set(all_backend) - hinted)

    report = {
        "client_route_count": len(mapped),
        "with_backend_candidate_existing": covered,
        "without_backend_candidate": len(no_backend),
        "routes": mapped,
        "routes_without_backend": [{"path": r["path"], "title": r["title"], "component": r["component"]} for r in no_backend],
        "backend_modules_total": len(all_backend),
        "backend_modules_not_hinted_by_client_routes": not_in_client_hints,
        "admin_api_ts_paths": scan_api_ts(),
        "note": "映射为路径启发式，不是运行时调用追踪；存在≠页面一定真调",
    }
    out = ROOT / "docs" / "probe_client_route_backend_map.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("CLIENT_ROUTES", len(mapped))
    print("WITH_BACKEND_HINT", covered, "WITHOUT", len(no_backend))
    print("--- client routes ---")
    for r in mapped:
        flag = "OK" if r["modules_exist"] else "??"
        print(f"{flag} {r['path']:42} {r['title'][:16]:16} -> {','.join(r['modules_exist'][:4]) or '-'}")
    print("WITHOUT_BACKEND")
    for r in no_backend:
        print(" ", r["path"], r["title"], r["component"])
    print("BACKEND_NOT_HINTED_COUNT", len(not_in_client_hints))
    print("written", out)


if __name__ == "__main__":
    main()
