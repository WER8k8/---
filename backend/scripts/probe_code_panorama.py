# -*- coding: utf-8 -*-
"""Code-only panorama probe. No design docs, no second brain."""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
APP = ROOT / "backend" / "app"
sys.path.insert(0, str(ROOT / "backend"))


def count_tables() -> int:
    tabs = set()
    for p in (APP / "models").glob("*.py"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        tabs.update(re.findall(r"__tablename__\s*=\s*[\"']([^\"']+)[\"']", t))
    return len(tabs)


def bridge_routers() -> list[str]:
    p = APP / "services" / "tasks" / "hermes_task_bridge.py"
    if not p.exists():
        return []
    t = p.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"ROUTERS:\s*dict[^\{]*\{(.*?)\n\}", t, re.S)
    if not m:
        return []
    return re.findall(r"[\"']([^\"']+)[\"']\s*:", m.group(1))


def acq_endpoints() -> list[str]:
    p = APP / "api" / "v1" / "routes" / "acquisition.py"
    t = p.read_text(encoding="utf-8", errors="ignore")
    eps = re.findall(r"@router\.(get|post|put|patch|delete)\(\s*[\"']([^\"']*)", t)
    return [f"{m.upper()} {path}" for m, path in eps]


def login_lock() -> dict:
    login = ROOT / "frontend/admin/src/views/login/index.vue"
    client_login = ROOT / "frontend/admin/src/views/client/login.vue"
    router = (ROOT / "frontend/admin/src/router/index.ts").read_text(encoding="utf-8", errors="ignore")
    return {
        "login_component_exists": login.exists(),
        "login_path_in_router": "path: '/login'" in router and "views/login/index.vue" in router,
        "client_login_vue_exists": client_login.exists(),
        "client_login_redirects": "path: '/client/login'" in router and "redirect: LOGIN_PATH" in router,
        "portal_alias_redirects": all(x in router for x in ["path: '/login/agent'", "path: '/login/partner'", "path: '/login/platform'"]),
        "shells": {
            "client": "path: '/client'" in router and "ClientShellLayout" in router,
            "admin_tenants_dashboard": "tenants/dashboard" in router or "TenantDashboard" in router,
            "partner": "path: '/partner'" in router,
            "agent": "path: '/agent'" in router,
        },
    }


def colors() -> dict:
    out = {}
    files = {
        "uiPreferences": ROOT / "frontend/admin/src/stores/uiPreferences.ts",
        "admin_tailwind": ROOT / "frontend/admin/tailwind.config.js",
        "web_css": ROOT / "frontend/assets/css/main.css",
    }
    for k, p in files.items():
        if not p.exists():
            out[k] = None
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        hits = re.findall(r"#(?:4a9b8c|2563eb|7c3aed|ea580c|0f172a)", t, flags=re.I)
        out[k] = {
            "has_mint": any(h.lower() == "#4a9b8c" for h in hits),
            "hits": hits[:20],
            "path": str(p.relative_to(ROOT)).replace("\\", "/"),
        }
    return out


def main() -> None:
    from app.services.hermes.executors import ExecutorRegistry
    from app.services.hermes import planner_service as ps
    from app.services.hermes.biz_bot_actions import MODULE_BUSINESS, coverage_report
    from app.services.aeos_registry import aeos_registry_report
    from app.services.desktop_hermes import desktop_hermes

    routes = [p for p in (APP / "api/v1/routes").glob("*.py") if not p.name.startswith("__")]
    route_re = re.compile(r"@router\.(get|post|put|patch|delete)\(")
    eps = 0
    top = []
    for p in routes:
        n = len(route_re.findall(p.read_text(encoding="utf-8", errors="ignore")))
        eps += n
        top.append((n, p.stem))
    top.sort(reverse=True)

    models_files = [p for p in (APP / "models").glob("*.py") if not p.name.startswith("__")]
    svc_files = list((APP / "services").rglob("*.py"))
    svc_domains = sorted(
        d.name for d in (APP / "services").iterdir() if d.is_dir() and d.name != "__pycache__"
    )
    exec_files = list((APP / "services/hermes/executors").glob("*_executor.py"))
    tests = list((ROOT / "backend/tests").rglob("test_*.py"))

    admin = ROOT / "frontend/admin/src"
    web = ROOT / "frontend"
    login_dir = admin / "views/login"

    skills = list((ROOT / "skills").glob("*/SKILL.md")) if (ROOT / "skills").exists() else []
    skill_names = [p.parent.name for p in sorted(skills)[:12]]

    ext_root = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\_external")
    ext = {}
    for name in ["trade-ai-agent", "goodjob-crm", "deer-flow", "ecc", "agency-agents-zh"]:
        p = ext_root / name
        ext[name] = {
            "exists": p.exists(),
            "files": sum(1 for x in p.rglob("*") if x.is_file()) if p.exists() else 0,
        }

    report = {
        "source": "code+runtime probe only (no second-brain / design docs as fact source)",
        "worktree": str(ROOT),
        "backend": {
            "route_modules": len(routes),
            "endpoints": eps,
            "top_modules": top[:12],
            "model_files": len(models_files),
            "sqlalchemy_tables": count_tables(),
            "service_py_files": len(svc_files),
            "service_domains": svc_domains,
            "executor_files": len(exec_files),
            "registered_executors": sorted(ExecutorRegistry.list_executors()),
            "registered_executor_count": len(ExecutorRegistry.list_executors()),
            "capability_count": len(ExecutorRegistry.capability_names()),
            "l1_templates": len(ps._TEMPLATES),
            "l1_first_keywords": [t[0][0] for t in ps._TEMPLATES],
            "biz_bot_coverage": coverage_report(),
            "biz_domain_mix": dict(Counter(s.domain for s in MODULE_BUSINESS.values())),
            "bridge_routers": bridge_routers(),
            "acquisition_endpoint_sample": acq_endpoints()[:20],
            "acquisition_endpoint_count": len(acq_endpoints()),
        },
        "aeos_registry_from_code": aeos_registry_report(),
        "desktop_hermes_status_from_code": desktop_hermes.status(),
        "frontend_admin": {
            "vue_views_total": len(list((admin / "views").rglob("*.vue"))) if (admin / "views").exists() else 0,
            "client_views": len(list((admin / "views/client").rglob("*.vue"))) if (admin / "views/client").exists() else 0,
            "admin_views": len(list((admin / "views/admin").rglob("*.vue"))) if (admin / "views/admin").exists() else 0,
            "agent_views": len(list((admin / "views/agent").rglob("*.vue"))) if (admin / "views/agent").exists() else 0,
            "partner_views": len(list((admin / "views/partner").rglob("*.vue"))) if (admin / "views/partner").exists() else 0,
            "tenants_views": len(list((admin / "views/tenants").rglob("*.vue"))) if (admin / "views/tenants").exists() else 0,
            "api_ts": len(list((admin / "api").rglob("*.ts"))) if (admin / "api").exists() else 0,
            "login_dir_files": [x.name for x in login_dir.iterdir()] if login_dir.exists() else [],
            "login_lock_probe": login_lock(),
        },
        "frontend_web": {
            "pages_vue": len(list((web / "pages").rglob("*.vue"))) if (web / "pages").exists() else 0,
            "components_vue": len(list((web / "components").rglob("*.vue"))) if (web / "components").exists() else 0,
            "has_nuxt_config": (web / "nuxt.config.ts").exists() or (web / "nuxt.config.js").exists(),
        },
        "colors_probe": colors(),
        "assets": {
            "skills_md": len(skills),
            "skill_sample": skill_names,
            "external": ext,
        },
        "tests": {"files": len(tests)},
    }
    import json

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
