# -*- coding: utf-8 -*-
"""Code-only slices: executors×caps, acquisition endpoints, PG empty tables, admin routes."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
APP = ROOT / "backend" / "app"
sys.path.insert(0, str(ROOT / "backend"))


def slice_executors() -> dict[str, Any]:
    from app.services.hermes.executors import ExecutorRegistry
    from app.services.hermes.biz_bot_actions import MODULE_BUSINESS

    names = sorted(ExecutorRegistry.list_executors())
    items = []
    for name in names:
        ex = ExecutorRegistry.get(name)
        caps = {}
        try:
            caps = dict(ex.get_capabilities() or {})
        except Exception as exc:  # noqa: BLE001
            caps = {"_error": str(exc)[:120]}
        # file path
        path = ""
        for p in (APP / "services/hermes/executors").glob("*_executor.py"):
            t = p.read_text(encoding="utf-8", errors="ignore")
            if re.search(rf"return\s+[\"']{re.escape(name)}[\"']", t):
                path = str(p.relative_to(ROOT)).replace("\\", "/")
                break
        items.append({
            "executor": name,
            "path": path,
            "capability_count": len([k for k in caps if not k.startswith("_")]),
            "capabilities": [
                {
                    "name": k,
                    "desc": (v or {}).get("desc", "") if isinstance(v, dict) else "",
                    "needs_approval": (v or {}).get("needs_approval") if isinstance(v, dict) else None,
                    "input": (v or {}).get("input") if isinstance(v, dict) else None,
                }
                for k, v in sorted(caps.items())
                if not str(k).startswith("_")
            ],
        })
    # modules bound to deep executors via biz_bot
    module_to_exec: dict[str, list[str]] = {}
    for mod, spec in MODULE_BUSINESS.items():
        module_to_exec.setdefault(spec.deep_executor, []).append(mod)
    return {
        "registered_count": len(names),
        "executors": items,
        "biz_bot_module_binding_counts": {k: len(v) for k, v in sorted(module_to_exec.items(), key=lambda x: -len(x[1]))},
    }


def slice_acquisition_endpoints() -> dict[str, Any]:
    path = APP / "api/v1/routes/acquisition.py"
    text = path.read_text(encoding="utf-8", errors="ignore")
    # capture decorator + following def name
    pattern = re.compile(
        r"@router\.(get|post|put|patch|delete)\(\s*[\"']([^\"']*)[\"'][^)]*\)\s*\n(?:\s*@[^\n]+\n)*\s*(?:async\s+)?def\s+(\w+)",
        re.M,
    )
    rows = []
    for m, path_s, fn in pattern.findall(text):
        rows.append({
            "method": m.upper(),
            "path": path_s,
            "function": fn,
            "full": f"{m.upper()} /api/v1/acquisition{path_s if path_s.startswith('/') else '/' + path_s}" if not path_s.startswith("http") else f"{m.upper()} {path_s}",
        })
    # fallback looser parse if few matches
    if len(rows) < 20:
        loose = re.findall(r"@router\.(get|post|put|patch|delete)\(\s*[\"']([^\"']*)[\"']", text)
        defs = re.findall(r"(?:async\s+)?def\s+(\w+)\(", text)
        rows = []
        for i, (m, p) in enumerate(loose):
            rows.append({
                "method": m.upper(),
                "path": p,
                "function": defs[i] if i < len(defs) else "",
                "full": f"{m.upper()} {p}",
            })
    # router prefix
    prefix = ""
    m = re.search(r"router\s*=\s*APIRouter\(([^)]*)\)", text, re.S)
    if m:
        pm = re.search(r"prefix\s*=\s*[\"']([^\"']+)[\"']", m.group(1))
        if pm:
            prefix = pm.group(1)
    return {
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "router_prefix": prefix,
        "count": len(rows),
        "endpoints": rows,
    }


def slice_pg_tables() -> dict[str, Any]:
    from sqlalchemy import text

    from app.core import config as app_config
    from app.core.database import SessionLocal, engine

    model_tables: set[str] = set()
    for p in (APP / "models").glob("*.py"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        model_tables.update(re.findall(r"__tablename__\s*=\s*[\"']([^\"']+)[\"']", t))

    out: dict[str, Any] = {
        "engine": str(engine.url),
        "dialect": engine.dialect.name,
        "settings_db_type": app_config.settings.DB_TYPE,
        "settings_database_url": app_config.settings.DATABASE_URL,
        "model_declared_tables": sorted(model_tables),
        "model_declared_count": len(model_tables),
    }
    if engine.dialect.name != "postgresql":
        out["error"] = "not_postgresql_cwd_must_be_backend"
        return out

    db = SessionLocal()
    try:
        pub_rows = db.execute(
            text(
                "select table_name from information_schema.tables "
                "where table_schema='public' and table_type='BASE TABLE' order by table_name"
            )
        ).fetchall()
        pub = [r[0] for r in pub_rows]
        dens = []
        for tname in pub:
            try:
                n = db.execute(text(f'select count(*) from "{tname}"')).scalar()
            except Exception as exc:  # noqa: BLE001
                n = None
                err = str(exc).splitlines()[0][:100]
            else:
                err = None
            dens.append({"table": tname, "rows": n, "error": err})
        empty = [d["table"] for d in dens if d["rows"] == 0]
        nonempty = [d for d in dens if isinstance(d["rows"], int) and d["rows"] > 0]
        nonempty.sort(key=lambda x: -x["rows"])
        out.update({
            "pg_public_tables": len(pub),
            "pg_table_names": pub,
            "density": dens,
            "empty_tables": empty,
            "empty_count": len(empty),
            "nonempty_top": nonempty[:40],
            "nonempty_count": len(nonempty),
            "in_models_not_in_pg": sorted(model_tables - set(pub)),
            "in_pg_not_in_models": sorted(set(pub) - model_tables),
        })
    finally:
        db.close()
    return out


def _parse_admin_routes(ts_path: Path) -> list[dict[str, Any]]:
    text = ts_path.read_text(encoding="utf-8", errors="ignore")
    # strip comments roughly
    rows: list[dict[str, Any]] = []

    # Find top-level route objects by scanning path: '...'
    # Also capture component import strings and redirect
    # We'll walk with a simple state for nesting depth of children arrays — lighter approach:
    # extract each `path: '...'` with nearby fields within ~400 chars
    for m in re.finditer(r"path:\s*['\"]([^'\"]+)['\"]", text):
        path = m.group(1)
        window = text[m.start(): m.start() + 500]
        name_m = re.search(r"name:\s*['\"]([^'\"]+)['\"]", window)
        title_m = re.search(r"title:\s*['\"]([^'\"]+)['\"]", window)
        comp_m = re.search(r"component:\s*\(\)\s*=>\s*import\(['\"]([^'\"]+)['\"]\)", window)
        redirect_m = re.search(r"redirect:\s*([^,\n]+)", window)
        # infer shell by path prefix
        shell = "public"
        if path.startswith("/client"):
            shell = "client"
        elif path.startswith("/admin") or path.startswith("/seo") or path.startswith("/tenants"):
            shell = "admin"
        elif path.startswith("/partner"):
            shell = "partner"
        elif path.startswith("/agent"):
            shell = "agent"
        elif path.startswith("/login"):
            shell = "login"
        rows.append({
            "path": path,
            "name": name_m.group(1) if name_m else "",
            "title": title_m.group(1) if title_m else "",
            "component": comp_m.group(1) if comp_m else "",
            "redirect": (redirect_m.group(1).strip() if redirect_m else ""),
            "shell": shell,
        })
    return rows


def slice_admin_routes() -> dict[str, Any]:
    router = ROOT / "frontend/admin/src/router/index.ts"
    gen = ROOT / "frontend/admin/src/router/generated-crud-routes.ts"
    rows = _parse_admin_routes(router)
    gen_rows = _parse_admin_routes(gen) if gen.exists() else []
    by_shell: dict[str, list[str]] = {}
    for r in rows:
        by_shell.setdefault(r["shell"], []).append(r["path"])
    # login lock facts
    text = router.read_text(encoding="utf-8", errors="ignore")
    return {
        "router_file": str(router.relative_to(ROOT)).replace("\\", "/"),
        "path_entries_index_ts": len(rows),
        "path_entries_generated_crud": len(gen_rows),
        "by_shell_counts": {k: len(v) for k, v in sorted(by_shell.items())},
        "by_shell_paths": {k: sorted(set(v)) for k, v in sorted(by_shell.items())},
        "login_lock": {
            "login_component": "frontend/admin/src/views/login/index.vue",
            "exists": (ROOT / "frontend/admin/src/views/login/index.vue").exists(),
            "client_login_vue_exists": (ROOT / "frontend/admin/src/views/client/login.vue").exists(),
            "redirects_to_LOGIN_PATH": [
                p for p in ["/client/login", "/login/agent", "/login/partner", "/login/platform", "/login/admin"]
                if f"path: '{p}'" in text and "redirect" in text[text.find(f"path: '{p}'"): text.find(f"path: '{p}'") + 80]
            ],
        },
        "all_routes": rows,
        "generated_crud_routes": gen_rows,
    }


def main() -> None:
    report = {
        "source": "code/runtime probe only",
        "cwd_note": "run with process cwd=backend for PG slice",
        "slice_executors": slice_executors(),
        "slice_acquisition": slice_acquisition_endpoints(),
        "slice_pg": slice_pg_tables(),
        "slice_admin_routes": slice_admin_routes(),
    }
    out = ROOT / "docs" / "code_probe_slices.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    # compact stdout summary
    ex = report["slice_executors"]
    acq = report["slice_acquisition"]
    pg = report["slice_pg"]
    ad = report["slice_admin_routes"]
    print("EXECUTORS", ex["registered_count"])
    for e in ex["executors"]:
        print(f"  {e['executor']}: caps={e['capability_count']} path={e['path']}")
    print("ACQ_COUNT", acq["count"], "prefix", acq["router_prefix"])
    for e in acq["endpoints"]:
        print(f"  {e['method']:6} {e['path']}  ({e['function']})")
    print("PG_DIALECT", pg.get("dialect"), "public", pg.get("pg_public_tables"), "empty", pg.get("empty_count"), "nonempty", pg.get("nonempty_count"))
    if pg.get("empty_tables"):
        print("PG_EMPTY", len(pg["empty_tables"]))
        for t in pg["empty_tables"]:
            print("  empty", t)
    if pg.get("in_models_not_in_pg"):
        print("MODEL_NOT_IN_PG", pg["in_models_not_in_pg"][:30], "count", len(pg["in_models_not_in_pg"]))
    if pg.get("in_pg_not_in_models"):
        print("PG_NOT_IN_MODEL_count", len(pg["in_pg_not_in_models"]))
    print("ADMIN_PATHS", ad["path_entries_index_ts"], "by_shell", ad["by_shell_counts"])
    print("written", out)


if __name__ == "__main__":
    main()
