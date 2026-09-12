#!/usr/bin/env python3
"""租户 L-Pro 预览站 SEO 审计（本地 dev · 无需公网 URL）。

检查项：
- Nuxt 租户页 200、非 500、有可见内容
- title / meta description / canonical / hreflang
- visitor-context：英文无微信渠道、气泡不含 WeChat
- 与 validate-no-fake-delivery 不冲突（只读探测）

Usage:
  python scripts/validate-tenant-seo-audit.py
  python scripts/validate-tenant-seo-audit.py --nuxt-base http://127.0.0.1:3000 --tenant dev.local
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "tenant-seo-audit-latest.json"

DEFAULT_NUXT = os.getenv("YOUDING_NUXT_BASE", "http://127.0.0.1:3000")
DEFAULT_API = os.getenv("YOUDING_API_BASE", "http://127.0.0.1:8001")


def _issue(severity: str, check: str, detail: str) -> dict[str, str]:
    return {"severity": severity, "check": check, "detail": detail}


def _fetch_html(client: httpx.Client, url: str) -> tuple[int, str, list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    try:
        r = client.get(url, follow_redirects=True)
    except Exception as exc:
        issues.append(_issue("P0", "nuxt_fetch", f"{url} — {exc}"[:240]))
        return 0, "", issues

    html = r.text or ""
    if r.status_code >= 500:
        issues.append(_issue("P0", "nuxt_status", f"HTTP {r.status_code} for {url}"))
    elif r.status_code >= 400:
        issues.append(_issue("P1", "nuxt_status", f"HTTP {r.status_code} for {url}"))

    title_m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    title = (title_m.group(1) if title_m else "").strip()
    if not title or title in {"Nuxt", "500 - Server Error | Nuxt", "500 - Vite Error | Nuxt"}:
        issues.append(_issue("P0", "title", f"missing or error title: {title!r}"))
    elif "500" in title and "Error" in title:
        issues.append(_issue("P0", "title", f"error page title: {title!r}"))

    if not re.search(r'<meta[^>]+name=["\']description["\']', html, re.I):
        issues.append(_issue("P1", "meta_description", "missing meta description"))

    if "lpro-root" not in html and "site-companion" not in html:
        issues.append(_issue("P0", "ssr_content", "no lpro-root / companion markup in HTML"))

    if not re.search(r'rel=["\']canonical["\']', html, re.I):
        issues.append(_issue("P2", "canonical", "no canonical link in HTML"))

    if not re.search(r'hreflang=', html, re.I):
        issues.append(_issue("P2", "hreflang", "no hreflang links in HTML"))

    return r.status_code, html, issues


def _api_reachable(client: httpx.Client, api_base: str) -> bool:
    try:
        r = client.get(f"{api_base.rstrip('/')}/api/v1/health", timeout=5.0)
        return r.status_code < 500
    except Exception:
        return False


def _check_visitor_context(
    client: httpx.Client,
    api_base: str,
    tenant: str,
    language: str,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    url = f"{api_base.rstrip('/')}/api/v1/public/tenants/{tenant}/visitor-context?language={language}"
    try:
        r = client.get(url)
        if r.status_code >= 300:
            issues.append(_issue("P0", f"visitor_context_{language}", f"HTTP {r.status_code}"))
            return issues
        body = r.json()
        data = body.get("data") if isinstance(body.get("data"), dict) else body
        if not isinstance(data, dict):
            issues.append(_issue("P0", f"visitor_context_{language}", "invalid JSON body"))
            return issues

        wangcai = data.get("wangcai_ui") or {}
        bubble = str(wangcai.get("bubble_3") or "")
        channels = data.get("contact_channels") or []
        types = [c.get("channel_type") for c in channels if isinstance(c, dict)]

        if language == "en":
            if re.search(r"WeChat|微信|QQ", bubble, re.I):
                issues.append(
                    _issue(
                        "P1",
                        "en_bubble_3",
                        f"English bubble still mentions CN IM: {bubble[:120]}",
                    )
                )
            if "wechat" in types or "qq" in types:
                issues.append(
                    _issue(
                        "P1",
                        "en_contact_channels",
                        f"English context should hide wechat/qq, got: {types}",
                    )
                )
        if language == "zh":
            if not bubble.strip():
                issues.append(_issue("P1", "zh_bubble_3", "missing bubble_3 for zh"))

        return issues
    except Exception as exc:
        issues.append(_issue("P0", f"visitor_context_{language}", str(exc)[:200]))
        return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Tenant preview SEO audit (local dev)")
    parser.add_argument("--nuxt-base", default=DEFAULT_NUXT)
    parser.add_argument("--api-base", default=DEFAULT_API)
    parser.add_argument("--tenant", default="dev.local")
    parser.add_argument("--lpro", default="1")
    parser.add_argument("--skip-api", action="store_true", help="Only audit Nuxt HTML (no visitor-context)")
    args = parser.parse_args()

    tenant_url = (
        f"{args.nuxt_base.rstrip('/')}/tenant"
        f"?__tenant={args.tenant}&lpro={args.lpro}"
    )
    en_url = f"{tenant_url}&language=en"

    all_issues: list[dict[str, str]] = []
    pages: dict[str, dict] = {}

    with httpx.Client(timeout=90.0, headers={"User-Agent": "YouDing-Tenant-SEO-Audit/1.0"}) as client:
        for label, url in (("zh_default", tenant_url), ("en", en_url)):
            status, _html, issues = _fetch_html(client, url)
            pages[label] = {"url": url, "status": status, "issue_count": len(issues)}
            all_issues.extend(issues)

        api_ok = _api_reachable(client, args.api_base)
        if args.skip_api or not api_ok:
            if not api_ok and not args.skip_api:
                all_issues.append(
                    _issue(
                        "P1",
                        "api_unreachable",
                        f"skip visitor-context — API not up at {args.api_base}",
                    )
                )
        else:
            for lang in ("zh", "en"):
                all_issues.extend(
                    _check_visitor_context(client, args.api_base, args.tenant, lang)
                )

    p0 = [i for i in all_issues if i["severity"] == "P0"]
    p1 = [i for i in all_issues if i["severity"] == "P1"]
    p2 = [i for i in all_issues if i["severity"] == "P2"]

    payload = {
        "ok": len(p0) == 0,
        "task": "TENANT-SEO-AUDIT",
        "tenant": args.tenant,
        "pages": pages,
        "summary": {"P0": len(p0), "P1": len(p1), "P2": len(p2)},
        "issues": all_issues,
        "out_of_scope": [
            "公网 URL 完整 site-audit（用 Admin /seo/site-audit）",
            "百度/Google 真实排名与收录",
        ],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
