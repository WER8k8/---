# -*- coding: utf-8 -*-
"""Nested admin route tree from router/index.ts (code-only)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
ROUTER = ROOT / "frontend/admin/src/router/index.ts"


def _extract_bracket_block(text: str, start_idx: int) -> str:
    """From a '[' after children: return balanced bracket block."""
    i = text.find("[", start_idx)
    if i < 0:
        return ""
    depth = 0
    for j in range(i, len(text)):
        ch = text[j]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[i : j + 1]
    return text[i:]


def _parse_route_objects(block: str, parent_path: str = "") -> list[dict]:
    """Parse route objects inside an array/object text block."""
    results: list[dict] = []
    # find objects starting with { that contain path:
    idx = 0
    while True:
        m = re.search(r"\{\s*\n?\s*path:\s*['\"]([^'\"]+)['\"]", block[idx:])
        if not m:
            break
        start = idx + m.start()
        # balance braces from start
        depth = 0
        end = None
        for j in range(start, len(block)):
            if block[j] == "{":
                depth += 1
            elif block[j] == "}":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        if end is None:
            break
        obj = block[start:end]
        raw_path = m.group(1)
        if raw_path.startswith("/"):
            full = raw_path
        else:
            base = parent_path.rstrip("/")
            full = f"{base}/{raw_path}" if base else f"/{raw_path}"
            full = re.sub(r"/+", "/", full)
        name_m = re.search(r"name:\s*['\"]([^'\"]+)['\"]", obj)
        title_m = re.search(r"title:\s*['\"]([^'\"]+)['\"]", obj)
        comp_m = re.search(r"component:\s*\(\)\s*=>\s*import\(['\"]([^'\"]+)['\"]\)", obj)
        redir_m = re.search(r"redirect:\s*([^,\n]+)", obj)
        meta_flags = {
            "requiresAuth": bool(re.search(r"requiresAuth:\s*true", obj)),
            "partnerShell": bool(re.search(r"partnerShell:\s*true", obj)),
            "agentShell": bool(re.search(r"agentShell:\s*true", obj)),
        }
        row = {
            "path": full,
            "raw_path": raw_path,
            "name": name_m.group(1) if name_m else "",
            "title": title_m.group(1) if title_m else "",
            "component": comp_m.group(1) if comp_m else "",
            "redirect": redir_m.group(1).strip() if redir_m else "",
            "parent": parent_path or "",
            **meta_flags,
        }
        results.append(row)
        # children
        cm = re.search(r"children:\s*", obj)
        if cm:
            child_block = _extract_bracket_block(obj, cm.end())
            if child_block.startswith("["):
                results.extend(_parse_route_objects(child_block[1:-1], full))
        idx = end
    return results


def shell_of(path: str) -> str:
    if path.startswith("/login"):
        return "login"
    if path.startswith("/client"):
        return "client"
    if path.startswith("/partner"):
        return "partner"
    if path.startswith("/agent"):
        return "agent"
    if path.startswith("/admin") or path.startswith("/tenants") or path.startswith("/seo"):
        return "admin"
    return "public"


def main() -> None:
    text = ROUTER.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"const\s+routes\s*:\s*RouteRecordRaw\[\]\s*=\s*", text)
    if not m:
        raise SystemExit("routes array not found")
    block = _extract_bracket_block(text, m.end())
    inner = block[1:-1] if block.startswith("[") else block
    routes = _parse_route_objects(inner, "")
    for r in routes:
        r["shell"] = shell_of(r["path"])

    by_shell: dict[str, list[str]] = {}
    for r in routes:
        by_shell.setdefault(r["shell"], []).append(r["path"])

    # generated crud
    gen_path = ROOT / "frontend/admin/src/router/generated-crud-routes.ts"
    gen_routes: list[dict] = []
    if gen_path.exists():
        gt = gen_path.read_text(encoding="utf-8", errors="ignore")
        gm = re.search(r"(?:export\s+)?const\s+\w+\s*:\s*RouteRecordRaw\[\]\s*=\s*", gt)
        if gm:
            gb = _extract_bracket_block(gt, gm.end())
            gi = gb[1:-1] if gb.startswith("[") else gb
            gen_routes = _parse_route_objects(gi, "")
            for r in gen_routes:
                r["shell"] = shell_of(r["path"])

    # login lock
    client_login_vue = ROOT / "frontend/admin/src/views/client/login.vue"
    login_vue = ROOT / "frontend/admin/src/views/login/index.vue"

    report = {
        "source": "router/index.ts nested parse (code-only)",
        "router_file": str(ROUTER.relative_to(ROOT)).replace("\\", "/"),
        "total_route_nodes": len(routes),
        "by_shell_counts": {k: len(v) for k, v in sorted(by_shell.items(), key=lambda x: -len(x[1]))},
        "login_lock": {
            "login_vue_exists": login_vue.exists(),
            "login_vue_path": "frontend/admin/src/views/login/index.vue",
            "client_login_vue_exists": client_login_vue.exists(),
            "login_route_component": next((r["component"] for r in routes if r["path"] == "/login"), ""),
            "alias_redirects": [
                r for r in routes
                if r["path"] in ("/client/login", "/login/agent", "/login/partner", "/login/platform", "/login/admin")
            ],
        },
        "routes": routes,
        "generated_crud_count": len(gen_routes),
        "generated_crud_routes": gen_routes,
        "by_shell_paths": {k: sorted(set(v)) for k, v in sorted(by_shell.items())},
    }
    out = ROOT / "docs" / "admin_route_tree.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("TOTAL_NODES", len(routes))
    print("BY_SHELL", report["by_shell_counts"])
    print("LOGIN", report["login_lock"]["login_route_component"], "client_login_vue", client_login_vue.exists())
    print("--- login ---")
    for r in routes:
        if r["shell"] == "login":
            print(f"  {r['path']} -> {r['redirect'] or r['component']}")
    print("--- client ---")
    for r in routes:
        if r["shell"] == "client":
            print(f"  {r['path']}  {r['title'] or r['name']}  {r['component']}")
    print("--- admin/tenants/seo ---")
    for r in routes:
        if r["shell"] == "admin":
            print(f"  {r['path']}  {r['title'] or r['name']}  {r['component']}")
    print("--- partner ---")
    for r in routes:
        if r["shell"] == "partner":
            print(f"  {r['path']}  {r['title'] or r['name']}")
    print("--- agent ---")
    for r in routes:
        if r["shell"] == "agent":
            print(f"  {r['path']}  {r['title'] or r['name']}")
    print("GEN_CRUD", len(gen_routes))
    print("written", out)


if __name__ == "__main__":
    main()
