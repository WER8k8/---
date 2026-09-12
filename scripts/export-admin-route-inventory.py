#!/usr/bin/env python3
"""导出 Admin 路由清单，供 PM×营销全环节审查对照。"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "frontend" / "admin" / "src" / "router" / "index.ts"

PATH_LINE = re.compile(r"path:\s*['\"]([^'\"]+)['\"]")
NAME_LINE = re.compile(r"name:\s*['\"]([^'\"]+)['\"]")
TITLE_LINE = re.compile(r"title:\s*['\"]([^'\"]+)['\"]")


def _shell(path: str) -> str:
    if path.startswith("/client"):
        return "client"
    if path in ("/landing", "/tenants/register", "/login", "/login/oauth-callback"):
        return "acquisition"
    if path.startswith("/admin") or "/admin/" in path:
        return "super_admin"
    if path.startswith("/agent"):
        return "agent"
    return "platform"


def main() -> int:
    if not ROUTER.is_file():
        print(f"missing router: {ROUTER}")
        return 1

    lines = ROUTER.read_text(encoding="utf-8", errors="replace").splitlines()
    routes: list[dict[str, str | bool | None]] = []
    seen: set[str] = set()

    for i, line in enumerate(lines):
        pm = PATH_LINE.search(line)
        if not pm:
            continue
        path = pm.group(1)
        if path.startswith("/:") or path in seen:
            continue
        seen.add(path)

        window = "\n".join(lines[i : min(i + 12, len(lines))])
        name_m = NAME_LINE.search(window)
        title_m = TITLE_LINE.search(window)
        is_redirect = "redirect:" in window.split("component:")[0] if "component:" in window else "redirect:" in window

        entry: dict[str, str | bool | None] = {
            "path": path,
            "name": name_m.group(1) if name_m else None,
            "title": title_m.group(1) if title_m else None,
            "shell": _shell(path),
        }
        if is_redirect:
            entry["redirect"] = True
        routes.append(entry)

    routes.sort(key=lambda r: str(r["path"]))
    by_shell: dict[str, int] = {}
    for r in routes:
        shell = str(r.get("shell") or "other")
        by_shell[shell] = by_shell.get(shell, 0) + 1

    out = {
        "task": "PM-MKT-01",
        "source": str(ROUTER.relative_to(ROOT)).replace("\\", "/"),
        "route_count": len(routes),
        "by_shell": by_shell,
        "routes": routes,
        "matrix_doc": "docs/pm-marketing-journey-review-matrix.md",
    }
    latest = ROOT / "docs" / "pm-marketing-route-inventory-latest.json"
    latest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {latest} ({len(routes)} routes)")
    for shell, n in sorted(by_shell.items()):
        print(f"  {shell}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
