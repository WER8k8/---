#!/usr/bin/env python3
"""Phase C step 1+2: hierarchy / aggregation API acceptance (browser regression proxy)."""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BASE = "http://127.0.0.1:8001"
ADMIN = "http://127.0.0.1:5173"
USERNAME = "admin"
PASSWORD = "admin123"


def check(name: str, ok: bool, detail: str = "") -> dict:
    return {"name": name, "ok": ok, "detail": detail}


def main() -> int:
    results: list[dict] = []
    token = None
    node_id = None

    with httpx.Client(base_url=BASE, timeout=20.0) as client:
        # 1 login
        try:
            r = client.post(
                "/api/v1/auth/login",
                json={"username_or_email": USERNAME, "password": PASSWORD},
            )
            body = r.json()
            data = body.get("data") or body
            token = data.get("access_token") or data.get("token")
            ok = r.status_code == 200 and bool(token)
            results.append(check("login", ok, f"status={r.status_code}"))
        except Exception as e:
            results.append(check("login", False, str(e)))
            _write_report(results)
            return 1

        headers = {"Authorization": f"Bearer {token}"}

        # 2 aggregation
        try:
            r = client.get("/api/v1/super-admin/aggregation", headers=headers)
            ok = r.status_code == 200 and r.json().get("code", 0) == 0
            results.append(check("aggregation_api", ok, f"status={r.status_code}"))
        except Exception as e:
            results.append(check("aggregation_api", False, str(e)))

        # 3 admin page reachable
        try:
            r = httpx.get(f"{ADMIN}/admin/aggregation", timeout=10.0, follow_redirects=True)
            results.append(check("aggregation_page", r.status_code == 200, f"status={r.status_code}"))
        except Exception as e:
            results.append(check("aggregation_page", False, str(e)))

        # 4 hierarchy list
        try:
            r = client.get("/api/v1/agent-tree/all-levels", headers=headers)
            payload = r.json()
            ok = r.status_code == 200 and payload.get("code", 0) == 0
            nodes = (payload.get("data") or {}).get("nodes") or []
            results.append(
                check("hierarchy_list", ok, f"status={r.status_code} nodes={len(nodes)}")
            )
        except Exception as e:
            results.append(check("hierarchy_list", False, str(e)))

        # 5 hierarchy CRUD smoke
        try:
            suffix = uuid.uuid4().hex[:6]
            l1 = client.post(
                "/api/v1/agent-tree/nodes",
                headers=headers,
                json={"name": f"accept-L1-{suffix}", "level": "l1", "is_active": True},
            )
            l1j = l1.json()
            if l1j.get("code") != 0:
                raise RuntimeError(f"L1 create failed: {l1j}")
            parent_id = l1j["data"]["id"]
            create = client.post(
                "/api/v1/agent-tree/nodes",
                headers=headers,
                json={
                    "name": f"accept-L2-{suffix}",
                    "level": "l2",
                    "parent_id": parent_id,
                    "is_active": True,
                },
            )
            cj = create.json()
            ok_create = create.status_code == 200 and cj.get("code") == 0
            if not ok_create:
                raise RuntimeError(f"L2 create failed: {cj}")
            node_id = cj["data"]["id"]
            upd = client.put(
                f"/api/v1/agent-tree/nodes/{node_id}",
                headers=headers,
                json={"name": f"accept-L2-{suffix}-edited"},
            )
            ok_update = upd.json().get("code") == 0
            dele = client.delete(f"/api/v1/agent-tree/nodes/{node_id}", headers=headers)
            ok_delete = dele.json().get("code") == 0
            results.append(
                check(
                    "hierarchy_crud",
                    ok_create and ok_update and ok_delete,
                    f"create={ok_create} update={ok_update} delete={ok_delete}",
                )
            )
        except Exception as e:
            results.append(check("hierarchy_crud", False, str(e)))

        # 6 hierarchy page
        try:
            r = httpx.get(f"{ADMIN}/admin/hierarchy", timeout=10.0, follow_redirects=True)
            results.append(check("hierarchy_page", r.status_code == 200, f"status={r.status_code}"))
        except Exception as e:
            results.append(check("hierarchy_page", False, str(e)))

    passed = all(x["ok"] for x in results)
    _write_report(results, passed)
    return 0 if passed else 1


def _write_report(results: list[dict], passed: bool | None = None) -> None:
    if passed is None:
        passed = all(x["ok"] for x in results)
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_api": BASE,
        "admin_ui": ADMIN,
        "passed": passed,
        "checks": results,
    }
    path = DOCS / "hierarchy-browser-acceptance-latest.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
