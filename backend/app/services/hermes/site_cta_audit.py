"""生成站双 CTA + 24h 询盘承诺抽检（western-inquiry-conversion）。"""

from __future__ import annotations

from typing import Any

_REQUIRED_HOME_KEYS = ("ctaPrimary", "ctaSecondary", "inquiryHook")
_24H_MARKERS = ("24 hour", "24 hours", "24h", "within 24", "24 小时", "24小时内")


def audit_site_western_cta(site_content: dict[str, Any]) -> dict[str, Any]:
    """返回 ok / issues，供建站流水线与送检脚本共用。"""
    issues: list[str] = []
    pages = site_content.get("pages") or {}
    home = pages.get("home") if isinstance(pages.get("home"), dict) else {}
    contact = pages.get("contact") if isinstance(pages.get("contact"), dict) else {}
    for key in _REQUIRED_HOME_KEYS:
        val = str(home.get(key) or "").strip()
        if not val:
            issues.append(f"home.{key} 缺失")

    primary = str(home.get("ctaPrimary") or "").strip()
    secondary = str(home.get("ctaSecondary") or "").strip()
    if primary and secondary and primary.lower() == secondary.lower():
        issues.append("home.ctaPrimary 与 ctaSecondary 不应相同")

    hook_blob = " ".join(
        [
            str(home.get("inquiryHook") or ""),
            str(contact.get("inquiryPrompt") or ""),
            str(home.get("description") or "")[:400],
        ]
    ).lower()
    if not any(m in hook_blob for m in _24H_MARKERS):
        issues.append("缺少 24h 回复承诺（inquiryHook / inquiryPrompt）")

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "cta_primary": primary or None,
        "cta_secondary": secondary or None,
        "spec": "western-inquiry-conversion",
    }
