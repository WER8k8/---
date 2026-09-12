#!/usr/bin/env python3
"""PM 巡检：Tier1 12 语种 visitor-context + 站点正文 i18n。"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import json
import sys
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

TIER1 = ["en", "zh", "ar", "es", "pt", "ru", "th", "vi", "id", "ms", "ja", "ko"]
EXPECTED_NAV = {
    "en": "Home",
    "zh": "首页",
    "ar": "الرئيسية",
    "es": "Inicio",
    "pt": "Início",
    "ru": "Главная",
    "th": "หน้าแรก",
    "vi": "Trang chủ",
    "id": "Beranda",
    "ms": "Laman Utama",
    "ja": "ホーム",
    "ko": "홈",
}
CRITICAL_UI_KEYS = [
    "nav_home",
    "nav_products",
    "nav_contact",
    "cta_primary",
    "inquiry_link",
    "lang_picker_label",
    "footer_copyright",
]


def fetch(domain: str, lang: str, host: str = "127.0.0.1:8001") -> dict:
    url = (
        f"http://{host}/api/v1/public/tenants/{domain}/visitor-context"
        f"?language={lang}"
    )
    with urllib.request.urlopen(url, timeout=12) as resp:
        body = json.load(resp)
    if body.get("code", 0) != 0:
        raise RuntimeError(f"API error lang={lang}: {body}")
    return body["data"]


def count_site_ui_keys(lang: str) -> int:
    from app.services.visitor_locale_service import SITE_UI

    en = SITE_UI.get("en", {})
    merged = {**en, **SITE_UI.get(lang, {})}
    return len(merged)


def main() -> int:
    domain = sys.argv[1] if len(sys.argv) > 1 else "dev.local"
    host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1:8001"

    en_data = fetch(domain, "en", host)
    en_title = (en_data.get("site_content_localized") or {}).get("home", {}).get("title", "")
    en_prod = ""
    pi = (en_data.get("site_content_localized") or {}).get("products", {}).get("productItems")
    if isinstance(pi, list) and pi:
        en_prod = str(pi[0].get("name", ""))

    en_ui_count = count_site_ui_keys("en")
    issues: list[str] = []
    from app.services.visitor_locale_service import SITE_UI

    logger.info('=== Tier1 audit: {domain} @ {host} ===\\n', domain, host)

    for lang in TIER1:
        try:
            d = fetch(domain, lang, host)
        except Exception as exc:
            logger.info('FAIL {lang}: {exc}', lang, exc)
            issues.append(f"{lang}: API failed")
            continue

        ui = d.get("site_ui") or {}
        nav = ui.get("nav_home", "")
        exp_nav = EXPECTED_NAV[lang]
        loc = d.get("site_content_localized") or {}
        home = loc.get("home") or {}
        products = loc.get("products") or {}
        title = str(home.get("title", ""))
        prod_items = products.get("productItems")
        prod = ""
        if isinstance(prod_items, list) and prod_items:
            prod = str(prod_items[0].get("name", ""))

        nav_ok = nav == exp_nav
        lang_ok = d.get("language") == lang
        ui_keys = len({**SITE_UI_EN_FALLBACK(ui), **ui})
        ui_coverage = ui_keys / en_ui_count if en_ui_count else 0

        content_ok = True
        if lang == "en":
            if "Manufacturer" not in title:
                content_ok = False
                issues.append(f"{lang}: hero missing Manufacturer")
            if "标准" in prod:
                content_ok = False
                issues.append(f"{lang}: product still Chinese")
        elif lang == "zh":
            if not any(x in title for x in ("生产", "厂家", "制造商")):
                content_ok = False
                issues.append(f"{lang}: hero not Chinese ({title[:50]})")
            if prod and "款" not in prod:
                issues.append(f"{lang}: product not Chinese ({prod})")
        else:
            if title == en_title:
                content_ok = False
                issues.append(f"{lang}: hero title unchanged vs EN")
            # 产品名：仅 en/zh 有 i18n 包；其余语种保留英文 SKU 为出口站惯例

        missing_critical = [k for k in CRITICAL_UI_KEYS if k not in ui and k not in SITE_UI.get("en", {})]
        # lang_picker_* 仅前端 FALLBACK，后端未全量收录时不计为缺陷
        missing_critical = [k for k in missing_critical if k not in ("lang_picker_label", "lang_more", "lang_tier2_disclaimer")]
        if missing_critical:
            issues.append(f"{lang}: missing site_ui keys {missing_critical}")

        status = "OK" if nav_ok and lang_ok and content_ok and not missing_critical else "ISSUE"
        line = (
            f"{status} [{lang}] nav_ok={nav_ok} lang_ok={lang_ok} content_ok={content_ok} "
            f"nav={nav} hero={title[:60]} product={prod[:40]}"
        )
        try:
            logger.info(line)
        except UnicodeEncodeError:
            logger.info('{status} [{lang}] nav_ok={nav_ok} lang_ok={lang_ok} content_ok={content_ok}', status, lang, nav_ok, lang_ok, content_ok)

    logger.info('\\n=== SITE_UI key coverage vs en ===')
    for lang in TIER1:
        n = count_site_ui_keys(lang)
        pct = round(100 * n / en_ui_count, 1) if en_ui_count else 0
        flag = "OK" if pct >= 99 or lang == "en" else ("PARTIAL" if pct >= 40 else "LOW")
        logger.info('  {flag} {lang}: {n}/{en_ui_count} ({pct}%)', flag, lang, n, en_ui_count, pct)

    report_path = BACKEND.parent / "docs" / "ops" / "tier1-language-audit-latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "domain": domain,
        "issues": issues,
        "languages": {},
    }
    for lang in TIER1:
        try:
            d = fetch(domain, lang, host)
            report["languages"][lang] = {
                "language": d.get("language"),
                "nav_home": (d.get("site_ui") or {}).get("nav_home"),
                "hero_title": (d.get("site_content_localized") or {}).get("home", {}).get("title"),
                "product_first": (
                    (d.get("site_content_localized") or {}).get("products", {}).get("productItems") or []
                )[0].get("name") if isinstance(
                    (d.get("site_content_localized") or {}).get("products", {}).get("productItems"), list
                ) and (d.get("site_content_localized") or {}).get("products", {}).get("productItems") else None,
            }
        except Exception as exc:
            report["languages"][lang] = {"error": str(exc)}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info('\\nReport: {report_path}', report_path)

    if issues:
        logger.info('"\\n=== Issues ({}) ===".format(len(issues))')
        for item in issues:
            logger.info('  - {item}', item)
        return 1

    logger.info('\\nAll Tier1 languages passed API audit.')
    return 0


def SITE_UI_EN_FALLBACK(ui: dict) -> dict:
    from app.services.visitor_locale_service import SITE_UI

    return {**SITE_UI.get("en", {}), **ui}


if __name__ == "__main__":
    raise SystemExit(main())
