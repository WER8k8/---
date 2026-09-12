#!/usr/bin/env python3
"""校验租户 L-Pro 三轨 SEO：API + 页面 head（需 backend :8001 + nuxt :3000）。"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request

UA = "Mozilla/5.0 YouDingDevCheck"
API = "http://127.0.0.1:8001/api/v1/public/tenants/dev.local/visitor-context"
PAGE = "http://localhost:3000/tenant?__tenant=dev.local&lpro=1&language=ru"


def fetch(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def check_api() -> dict:
    out: dict[str, dict[str, str]] = {}
    for lang in ("en", "zh", "ru"):
        raw = fetch(f"{API}?language={lang}", timeout=15)
        data = json.loads(raw).get("data", {})
        home = data.get("site_content_localized", {}).get("home", {})
        out[lang] = {
            "title": str(home.get("title") or ""),
            "seoDescription": str(home.get("seoDescription") or ""),
            "seoKeywords": str(home.get("seoKeywords") or ""),
        }
    return out


def check_html() -> dict:
    html = fetch(PAGE, timeout=180)
    title = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    desc = re.search(
        r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"']([^\"']*)[\"']",
        html,
        re.I,
    )
    if not desc:
        desc = re.search(
            r"<meta[^>]+content=[\"']([^\"']*)[\"'][^>]+name=[\"']description[\"']",
            html,
            re.I,
        )
    kw = re.search(
        r"<meta[^>]+name=[\"']keywords[\"'][^>]+content=[\"']([^\"']*)[\"']",
        html,
        re.I,
    )
    hreflangs = re.findall(
        r"<link[^>]+rel=[\"']alternate[\"'][^>]+hreflang=[\"']([^\"']+)[\"'][^>]+href=[\"']([^\"']+)[\"']",
        html,
        re.I,
    )
    canon = re.search(
        r"<link[^>]+rel=[\"']canonical[\"'][^>]+href=[\"']([^\"']+)[\"']",
        html,
        re.I,
    )
    return {
        "bytes": len(html),
        "title": title.group(1) if title else "",
        "description": desc.group(1) if desc else "",
        "keywords": kw.group(1) if kw else "",
        "canonical": canon.group(1) if canon else "",
        "hreflangs": [{"hreflang": hl, "href": href} for hl, href in hreflangs],
    }


def main() -> int:
    errors: list[str] = []
    print("=== 1) ensure_dev_sqlite 已跑；API visitor-context ===")
    try:
        api = check_api()
    except Exception as e:
        print(f"API FAIL: {e}")
        return 1
    for lang, row in api.items():
        print(f"\n[{lang}]")
        print(f"  title: {row['title']}")
        print(f"  seoDescription: {row['seoDescription'][:100]}")
        print(f"  seoKeywords: {row['seoKeywords'][:80]}")
        if not row["seoDescription"]:
            errors.append(f"API {lang}: missing seoDescription")

    ru = api.get("ru", {})
    if "производитель" not in ru.get("seoDescription", "").lower() and "Производитель" not in ru.get("title", ""):
        errors.append("API ru: expected Russian SEO text")
    if "生产厂家" not in api.get("zh", {}).get("title", ""):
        errors.append("API zh: expected Chinese title")
    if "Manufacturer" not in api.get("en", {}).get("title", ""):
        errors.append("API en: expected English title")

    print("\n=== 2) Nuxt 页面 head (?language=ru) ===")
    try:
        head = check_html()
    except Exception as e:
        print(f"PAGE FAIL: {e}")
        errors.append(f"PAGE: {e}")
        head = {}

    if head:
        print(f"bytes: {head['bytes']}")
        print(f"title: {head['title']}")
        print(f"description: {head['description'][:120]}")
        print(f"keywords: {head['keywords'][:100]}")
        print(f"canonical: {head['canonical']}")
        for item in head.get("hreflangs", []):
            print(f"  hreflang {item['hreflang']}: {item['href'][:95]}")
        if "language=ru" not in head.get("canonical", ""):
            errors.append("HTML: canonical missing language=ru")
        hl_codes = {x["hreflang"] for x in head.get("hreflangs", [])}
        for need in ("en", "zh-CN", "ru", "x-default"):
            if need not in hl_codes:
                errors.append(f"HTML: missing hreflang {need}")
        if "Производитель" not in head.get("title", "") and "Export Products" not in head.get("title", ""):
            errors.append("HTML: title does not look Russian/export")

    if errors:
        print("\nFAIL:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("\nOK: API 三轨 SEO + 页面 ru head/hreflang 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
