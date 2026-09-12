"""租户建站设计 manifest 与设计门禁（供 Hermes 流水线复用，避免循环 import）。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.site_ai_service import build_template_site_content

_MANIFEST_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "tenant_site_design_manifest.json"
)


@lru_cache(maxsize=1)
def load_design_manifest() -> dict[str, Any]:
    """load_design_manifest。
    :return: 返回处理结果。
    """
    with open(_MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def _pick_allowed_color(key: str, value: str | None, manifest: dict[str, Any]) -> str:
    """_pick_allowed_color。

    参数说明：
    :param key: 参数 key
    :param value: 参数 value
    :param manifest: 参数 manifest
    :return: 返回处理结果。
    """
    allowed = (manifest.get("allowed_theme_colors") or {}).get(key) or []
    defaults = manifest.get("default_theme") or {}
    if value and value.lower() in {c.lower() for c in allowed}:
        return value
    if value in allowed:
        return value
    return str(defaults.get(key) or allowed[0] if allowed else "#1e293b")


def apply_design_guard(site_content: dict[str, Any]) -> dict[str, Any]:
    """按设计 manifest 校正 theme / 文案禁区 / 结构。"""
    manifest = load_design_manifest()
    out = json.loads(json.dumps(site_content, ensure_ascii=False))
    theme = out.get("theme") if isinstance(out.get("theme"), dict) else {}
    for key in ("headerBg", "heroBg", "footerBg"):
        theme[key] = _pick_allowed_color(key, theme.get(key), manifest)
    header = theme.get("headerBg")
    theme["footerBg"] = header
    out["theme"] = theme
    forbidden = manifest.get("forbidden_copy_patterns") or []
    pages = out.get("pages") if isinstance(out.get("pages"), dict) else {}
    for page_key, page in pages.items():
        if not isinstance(page, dict):
            continue
        for field, val in list(page.items()):
            if not isinstance(val, str):
                continue
            cleaned = val
            for word in forbidden:
                cleaned = cleaned.replace(word, "")
            page[field] = cleaned.strip()
        pages[page_key] = page
    out["pages"] = pages
    for key in manifest.get("page_keys") or []:
        if key not in pages or not isinstance(pages.get(key), dict):
            template_pages = build_template_site_content(
                out.get("brand", {}).get("name") or "产品", ""
            ).get("pages", {})
            pages[key] = template_pages.get(key, {})
    out["pages"] = pages
    return out
