"""P0-08：前端 super-admin 引用与 FastAPI 挂载路径对齐审计。"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FRONTEND_ADMIN = ROOT / "frontend" / "admin"

_PATTERN = re.compile(
    r"""['"](/api/v1/super-admin[^'"]+)['"]|"""
    r"""['"](/super-admin[^'"]+)['"]|"""
    r"""apiGet\(\s*['"](/super-admin[^'"]+)['"]"""
)


def collect_frontend_paths() -> set[str]:
    """collect_frontend_paths。
    :return: 返回处理结果。
    """
    found: set[str] = set()
    if not FRONTEND_ADMIN.is_dir():
        return found
    for ext in ("*.vue", "*.ts", "*.js"):
        for path in FRONTEND_ADMIN.rglob(ext):
            if "node_modules" in path.parts or "dist" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for m in _PATTERN.finditer(text):
                p = m.group(1) or m.group(2) or m.group(3)
                if p.startswith("/api/v1"):
                    p = p[len("/api/v1") :]
                if p.startswith("/super-admin"):
                    found.add(p.split("?")[0].rstrip("/"))
    return found


def collect_mounted_paths() -> set[str]:
    """collect_mounted_paths。
    :return: 返回处理结果。
    """
    from app.main import app
    out: set[str] = set()
    for route in app.routes:
        p = (getattr(route, "path", "") or "").rstrip("/")
        if "/super-admin" in p:
            if p.startswith("/api/v1"):
                p = p[len("/api/v1") :]
            out.add(p)
    return out


def path_matches(call: str, mounted: set[str]) -> bool:
    """path_matches。

    参数说明：
    :param call: 参数 call
    :param mounted: 参数 mounted
    :return: 返回处理结果。
    """
    if call in mounted:
        return True
    for m in mounted:
        if m.startswith(call + "/") or call.startswith(m + "/"):
            return True
        if "{" in m:
            prefix = m.split("{")[0].rstrip("/")
            if call.startswith(prefix):
                return True
    return False


def run_super_admin_path_audit() -> dict:
    """返回审计结果，供运维 API 与就绪检查使用。"""
    frontend = collect_frontend_paths()
    mounted = collect_mounted_paths()
    missing = sorted(p for p in frontend if not path_matches(p, mounted))
    return {
        "frontend_refs": len(frontend),
        "mounted_routes": len(mounted),
        "missing_count": len(missing),
        "missing_paths": missing[:50],
        "ok": len(missing) == 0,
    }
