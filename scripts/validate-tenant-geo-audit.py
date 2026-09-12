#!/usr/bin/env python3
"""租户预览站 GEO/AEO 审计（llms.txt · JSON-LD · AI 爬虫语义块 · 统一 GEO 分）。

Usage:
  python scripts/validate-tenant-geo-audit.py
  python scripts/validate-tenant-geo-audit.py --skip-probes
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
REPORT = ROOT / "docs" / "tenant-geo-audit-latest.json"

DEFAULT_NUXT = os.getenv("YOUDING_NUXT_BASE", "http://127.0.0.1:3000")
DEFAULT_API = os.getenv("YOUDING_API_BASE", "http://127.0.0.1:8001")
AI_UA = "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)"


def _issue(severity: str, check: str, detail: str) -> dict[str, str]:
    return {"severity": severity, "check": check, "detail": detail}


def _api_reachable(client: httpx.Client, api_base: str) -> bool:
    try:
        r = client.get(f"{api_base.rstrip('/')}/api/v1/health", timeout=5.0)
        return r.status_code < 500
    except Exception:
        return False


def _get_with_retry(client: httpx.Client, url: str, *, headers: dict | None = None, attempts: int = 3) -> httpx.Response:
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return client.get(url, headers=headers)
        except Exception as exc:
            last_exc = exc
            if i + 1 >= attempts:
                raise
            import time

            time.sleep(1.5)
    raise last_exc  # pragma: no cover


def main() -> int:
    parser = argparse.ArgumentParser(description="Tenant preview GEO audit")
    parser.add_argument("--nuxt-base", default=DEFAULT_NUXT)
    parser.add_argument("--api-base", default=DEFAULT_API)
    parser.add_argument("--tenant", default="dev.local")
    parser.add_argument("--skip-probes", action="store_true")
    args = parser.parse_args()

    issues: list[dict[str, str]] = []
    checks: dict[str, object] = {}

    tenant_q = f"__tenant={args.tenant}&lpro=1"
    llms_url = f"{args.nuxt_base.rstrip('/')}/llms.txt?{tenant_q}"
    llms_full_url = f"{args.nuxt_base.rstrip('/')}/llms-full.txt?{tenant_q}"
    tenant_page = f"{args.nuxt_base.rstrip('/')}/tenant?{tenant_q}"

    with httpx.Client(timeout=90.0, headers={"User-Agent": "YouDing-Tenant-GEO-Audit/1.0"}) as client:
        for label, url in (("llms_txt", llms_url), ("llms_full", llms_full_url)):
            try:
                r = _get_with_retry(client, url)
                body = r.text or ""
                checks[label] = {"url": url, "status": r.status_code, "bytes": len(body)}
                if r.status_code >= 400:
                    issues.append(_issue("P0", label, f"HTTP {r.status_code}"))
                elif len(body) < 80:
                    issues.append(_issue("P1", label, f"content too short ({len(body)} bytes)"))
                elif "# LLMs.txt" not in body and "LLMs.txt" not in body:
                    issues.append(_issue("P1", label, "missing LLMs.txt header"))
            except Exception as exc:
                issues.append(_issue("P0", label, str(exc)[:200]))

        try:
            r = _get_with_retry(client, tenant_page)
            html = r.text or ""
            checks["tenant_html"] = {"status": r.status_code, "bytes": len(html)}
            if r.status_code >= 400:
                issues.append(_issue("P0", "tenant_html", f"HTTP {r.status_code}"))
            elif 'application/ld+json' not in html and "schema.org" not in html:
                issues.append(_issue("P1", "json_ld", "no JSON-LD in SSR HTML"))
        except Exception as exc:
            issues.append(_issue("P0", "tenant_html", str(exc)[:200]))

        try:
            r = _get_with_retry(client, tenant_page, headers={"User-Agent": AI_UA})
            bot_html = r.text or ""
            checks["ai_crawler_html"] = {"status": r.status_code, "bytes": len(bot_html)}
            if r.status_code >= 400:
                issues.append(_issue("P0", "ai_crawler", f"HTTP {r.status_code}"))
            elif "ai-semantic-payload" not in bot_html:
                issues.append(
                    _issue(
                        "P1",
                        "ai_semantic_payload",
                        "GPTBot UA 未注入 ai-semantic-payload（需 Nuxt ai-crawler middleware）",
                    )
                )
        except Exception as exc:
            issues.append(_issue("P1", "ai_crawler", str(exc)[:200]))

        if _api_reachable(client, args.api_base) and not args.skip_probes:
            score_url = (
                f"{args.api_base.rstrip('/')}/api/v1/public/tenants/{args.tenant}/geo-score"
                "?include_probes=false"
            )
            try:
                r = client.get(score_url)
                if r.status_code >= 400:
                    issues.append(_issue("P0", "unified_geo_score", f"HTTP {r.status_code}"))
                else:
                    body = r.json()
                    data = body.get("data") if isinstance(body.get("data"), dict) else body
                    schema = str((data or {}).get("schema_version") or "")
                    overall = (data or {}).get("overall")
                    checks["unified_geo_score"] = {
                        "schema_version": schema,
                        "overall": overall,
                    }
                    if schema != "unified-geo-v1":
                        issues.append(_issue("P1", "geo_score_schema", f"unexpected schema {schema!r}"))
                    if overall is None:
                        issues.append(_issue("P1", "geo_score_overall", "missing overall score"))
            except Exception as exc:
                issues.append(_issue("P0", "unified_geo_score", str(exc)[:200]))

            probe_url = f"{args.api_base.rstrip('/')}/api/v1/public/tenants/{args.tenant}/ai-search-probes"
            try:
                r = client.get(probe_url)
                if r.status_code >= 400:
                    issues.append(_issue("P1", "ai_search_probes", f"HTTP {r.status_code}"))
                else:
                    body = r.json()
                    data = body.get("data") if isinstance(body.get("data"), dict) else body
                    models = (data or {}).get("models") or []
                    checks["ai_search_probes"] = {
                        "count": len(models),
                        "ids": [m.get("id") for m in models if isinstance(m, dict)],
                    }
                    ids = {m.get("id") for m in models if isinstance(m, dict)}
                    if "perplexity" not in ids or "copilot" not in ids:
                        issues.append(_issue("P1", "ai_search_probes", f"missing probes in {ids}"))
            except Exception as exc:
                issues.append(_issue("P1", "ai_search_probes", str(exc)[:200]))
        elif not _api_reachable(client, args.api_base):
            issues.append(
                _issue("P1", "api_unreachable", f"skip geo-score — API down at {args.api_base}")
            )

    p0 = [i for i in issues if i["severity"] == "P0"]
    p1 = [i for i in issues if i["severity"] == "P1"]

    payload = {
        "ok": len(p0) == 0,
        "task": "TENANT-GEO-AUDIT",
        "tenant": args.tenant,
        "checks": checks,
        "summary": {"P0": len(p0), "P1": len(p1)},
        "issues": issues,
        "score_contract": "unified-geo-v1",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
