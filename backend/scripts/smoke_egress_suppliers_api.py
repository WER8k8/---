"""Smoke-test /api/v1/egress/suppliers with admin login."""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8001/api/v1"


def post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def get(path: str, token: str) -> tuple[int, dict]:
    req = urllib.request.Request(
        f"{BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return exc.code, parsed


def main() -> None:
    login = post("/auth/login", {"username_or_email": "admin", "password": "admin123"})
    token = (login.get("data") or {}).get("access_token") or login.get("access_token")
    if not token:
        logger.info('"LOGIN_FAIL", json.dumps(login, ensure_ascii=False)[:500]')
        return
    status, body = get("/egress/suppliers", token)
    logger.info('"HTTP", status')
    if status != 200:
        logger.info(json.dumps(body, ensure_ascii=False)[:800])
        return
    providers = (body.get("data") or {}).get("providers") or body.get("providers")
    logger.info('"providers_count", len(providers or [])')
    for p in providers or []:
        logger.info('" ", p.get("code"), p.get("name"), "active=", p.get("is_active")')


if __name__ == "__main__":
    main()
