# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""开发信可达性 — 质量评分、垃圾箱风险、发送窗口（研究员×PM 契约）。"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

try:
    from email_validator import EmailNotValidError, validate_email as _validate_email_rfc
except ImportError:  # pragma: no cover
    EmailNotValidError = ValueError  # type: ignore[misc, assignment]

    def _validate_email_rfc(value: str, /, **_: Any) -> Any:
        """_validate_email_rfc。

        参数说明：
        :param **_: 参数 **_
        :return: 返回处理结果。
        """
        raise ImportError("email-validator not installed")

# ISO 3166-1 alpha-2 → IANA 时区（买家本地发送窗口用）
_COUNTRY_TZ: dict[str, str] = {
    "SA": "Asia/Riyadh",
    "AE": "Asia/Dubai",
    "QA": "Asia/Qatar",
    "KW": "Asia/Kuwait",
    "OM": "Asia/Muscat",
    "VN": "Asia/Ho_Chi_Minh",
    "TH": "Asia/Bangkok",
    "MY": "Asia/Kuala_Lumpur",
    "ID": "Asia/Jakarta",
    "PH": "Asia/Manila",
    "IN": "Asia/Kolkata",
    "BD": "Asia/Dhaka",
    "PK": "Asia/Karachi",
    "NG": "Africa/Lagos",
    "KE": "Africa/Nairobi",
    "EG": "Africa/Cairo",
    "ZA": "Africa/Johannesburg",
    "MX": "America/Mexico_City",
    "BR": "America/Sao_Paulo",
    "CL": "America/Santiago",
    "US": "America/New_York",
    "DE": "Europe/Berlin",
    "PL": "Europe/Warsaw",
    "GB": "Europe/London",
    "FR": "Europe/Paris",
    "XX": "UTC",
}

# 触发垃圾过滤器的高风险词（中英）
_SPAM_TRIGGERS: tuple[str, ...] = (
    "免费",
    "限时",
    "100%",
    " guaranteed ",
    "act now",
    "click here",
    "buy now",
    "!!!",
    "恭喜",
    "中奖",
    "urgent",
    "limited time",
    "no obligation",
    "risk-free",
    "make money",
    "最低价",
    "全网最低",
    "Dear Sir/Madam",
    "最佳报价",
    "立即下单",
)

_SUBJECT_SPAM: tuple[str, ...] = (
    "【",
    "】",
    "Re: Re:",
    "FREE",
    "URGENT",
    "!!!",
    "?",
)

_WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri")


def country_timezone(country_code: str | None) -> str:
    """country_timezone。

    参数说明：
    :param country_code: 参数 country_code
    :return: 返回处理结果。
    """
    cc = (country_code or "XX").upper()[:2]
    return _COUNTRY_TZ.get(cc, "UTC")


def suggest_send_window(
    country_code: str | None,
    *,
    from_utc: datetime | None = None,
) -> dict[str, Any]:
    """
    下一个买家本地工作日上午 9:30–11:00 的发送建议（避开周末）。
    返回 UTC ISO 时间供队列/日历使用。
    """
    now = from_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    tz_name = country_timezone(country_code)
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    local = now.astimezone(tz)
    candidate = local.replace(hour=10, minute=0, second=0, microsecond=0)
    if candidate <= local:
        candidate += timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    send_utc = candidate.astimezone(timezone.utc)
    return {
        "country_code": (country_code or "XX").upper()[:2],
        "timezone": tz_name,
        "local_window": "09:30–11:00 Tue–Thu preferred; avoid Fri PM & weekends",
        "suggested_send_at_utc": send_utc.isoformat(),
        "suggested_local_label": candidate.strftime("%Y-%m-%d %H:%M %Z"),
        "follow_up_days": [3, 7],
    }


def follow_up_schedule(first_send_utc_iso: str) -> list[dict[str, str]]:
    """首轮发送后的跟进节奏（仅建议，不自动发）。"""
    try:
        base = datetime.fromisoformat(first_send_utc_iso.replace("Z", "+00:00"))
    except ValueError:
        base = datetime.now(timezone.utc)
    out: list[dict[str, str]] = []
    for day in (3, 7):
        t = base + timedelta(days=day)
        while t.weekday() >= 5:
            t += timedelta(days=1)
        out.append(
            {
                "day_offset": str(day),
                "send_at_utc": t.isoformat(),
                "purpose": "gentle_follow_up" if day == 3 else "final_value_add",
            }
        )
    return out


def check_recipient_email(email: str | None) -> dict[str, Any]:
    """RFC 邮箱校验（email-validator）；不探测 MX，避免假「可达」。"""
    raw = (email or "").strip()
    if not raw:
        return {
            "email": raw,
            "syntax_ok": False,
            "normalized": None,
            "issues": [{"code": "missing", "detail": "未填写收件邮箱"}],
        }
    try:
        info = _validate_email_rfc(raw, check_deliverability=False)
        normalized = info.normalized
    except EmailNotValidError as exc:
        return {
            "email": raw,
            "syntax_ok": False,
            "normalized": None,
            "issues": [{"code": "invalid_syntax", "detail": str(exc)}],
        }
    except ImportError:
        ok = bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", raw))
        return {
            "email": raw,
            "syntax_ok": ok,
            "normalized": raw.lower() if ok else None,
            "issues": [] if ok else [{"code": "invalid_syntax", "detail": "格式不符"}],
            "validator": "regex_fallback",
        }
    issues: list[dict[str, str]] = []
    local = normalized.split("@", 1)[0]
    if local.startswith("noreply") or local in {"info", "sales", "support", "contact"}:
        issues.append(
            {
                "code": "role_address",
                "detail": f"角色邮箱 {local}@…，回复率通常低于决策人直邮",
                "fix": "优先采购/Import/Procurement 具名邮箱",
            }
        )
    disposable_domains = ("mailinator.com", "tempmail.com", "guerrillamail.com")
    domain = normalized.rsplit("@", 1)[-1]
    if domain in disposable_domains:
        issues.append(
            {
                "code": "disposable_domain",
                "detail": "一次性邮箱域名",
                "fix": "勿计入 A 类潜客",
            }
        )
    return {
        "email": raw,
        "syntax_ok": True,
        "normalized": normalized,
        "issues": issues,
        "validator": "email_validator",
    }


def scan_spam_risks(text: str) -> list[dict[str, str]]:
    """扫描正文/主题中的垃圾箱触发项。"""
    risks: list[dict[str, str]] = []
    lower = (text or "").lower()
    for word in _SPAM_TRIGGERS:
        if word.strip().lower() in lower or word in (text or ""):
            risks.append(
                {
                    "code": "spam_trigger",
                    "detail": f"含高风险词或模板句：{word.strip()}",
                    "fix": "改为具体规格/项目语境，避免促销腔",
                }
            )
    if len(re.findall(r"!", text or "")) >= 2:
        risks.append(
            {
                "code": "exclamation",
                "detail": "感叹号过多",
                "fix": "商务开发信建议零或一个句号结尾",
            }
        )
    if re.search(r"https?://", text or ""):
        n = len(re.findall(r"https?://", text))
        if n > 1:
            risks.append(
                {
                    "code": "too_many_links",
                    "detail": f"链接 {n} 个，易进推广箱",
                    "fix": "首封仅 1 个独立域或签名档链接",
                }
            )
    caps = re.findall(r"\b[A-Z]{4,}\b", text or "")
    if len(caps) >= 3:
        risks.append(
            {
                "code": "shouting_caps",
                "detail": "全大写词过多",
                "fix": "仅保留规格缩写（如 MOQ、FOB）",
            }
        )
    return risks


def polish_subject(subject: str, *, product: str, country_code: str) -> str:
    """主题行专业化：去括号促销感、控制长度。"""
    s = (subject or "").strip()
    s = s.replace("【", "").replace("】", "")
    s = re.sub(r"!+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > 72:
        s = s[:69] + "..."
    if not s or s.startswith("Re: Re:"):
        cc = (country_code or "export").upper()[:2]
        prod = (product or "building materials")[:40]
        s = f"{prod} specs — {cc} project supply"
    return s


def score_letter_quality(
    *,
    subject: str,
    body: str,
    has_prospect_name: bool,
) -> dict[str, Any]:
    """0–100 质量分 + 是否允许进入「待发送」队列。"""
    risks = scan_spam_risks(subject + "\n" + body)
    score = 100
    score -= min(40, len(risks) * 12)
    words = len(re.findall(r"\w+", body or ""))
    if words < 60:
        score -= 15
    if words > 280:
        score -= 10
    if not has_prospect_name and "Dear Sir/Madam" in (body or ""):
        score -= 8
    if re.search(r"(MOQ|FOB|spec|规格|防火|insulation)", body or "", re.I):
        score += 5
    score = max(0, min(100, score))
    return {
        "score": score,
        "grade": "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D",
        "send_ready": score >= 70 and len(risks) <= 1,
        "risks": risks,
    }


def deliverability_checklist(*, tenant_has_custom_domain: bool = False) -> list[dict[str, str]]:
    """发信前基础设施清单（PM：真发前必过）。"""
    rows = [
        {
            "item": "SPF 记录",
            "status": "manual",
            "note": "发信域名 DNS 已配置 SPF，含实际 SMTP 服务商",
        },
        {
            "item": "DKIM 签名",
            "status": "manual",
            "note": "邮箱服务商已开启 DKIM，选择器与 DNS 一致",
        },
        {
            "item": "DMARC",
            "status": "manual",
            "note": "建议 p=none 起步，稳定后 quarantine",
        },
        {
            "item": "发信域名",
            "status": "pass" if tenant_has_custom_domain else "warn",
            "note": "独立域子域（如 mail.yourbrand.com）优于免费邮箱",
        },
        {
            "item": "域名预热",
            "status": "manual",
            "note": "新域名首周 ≤20 封/日，逐周加倍",
        },
        {
            "item": "Plain-text 副本",
            "status": "auto",
            "note": "系统已生成纯文本友好结构；HTML 邮件需另附 text/plain",
        },
        {
            "item": "退订/地址",
            "status": "manual",
            "note": "批量开发信需物理地址 + 退订链接（CAN-SPAM/GDPR）",
        },
        {
            "item": "首封链接数",
            "status": "auto",
            "note": "建议 ≤1 个；勿附超大附件",
        },
    ]
    return rows


def enrich_letter(
    letter: dict[str, Any],
    *,
    product: str,
    country_code: str,
    company_name: str,
    recipient_email: str | None = None,
) -> dict[str, Any]:
    """为单封开发信附加可达性元数据并润色主题。"""
    out = dict(letter)
    subj = out.get("subject") or out.get("subject_en") or out.get("subject_zh") or ""
    body = out.get("body") or out.get("body_en") or out.get("body_zh") or ""
    out["subject"] = polish_subject(subj, product=product, country_code=country_code)
    if "subject_en" in out:
        out["subject_en"] = polish_subject(
            out.get("subject_en") or subj, product=product, country_code=country_code
        )
    if "subject_zh" in out:
        out["subject_zh"] = polish_subject(
            out.get("subject_zh") or subj, product=product, country_code=country_code
        )
    has_name = bool(re.search(r"Dear\s+[A-Z][a-z]+", body))
    quality = score_letter_quality(subject=out["subject"], body=body, has_prospect_name=has_name)
    send_hint = suggest_send_window(country_code)
    recipient_check = check_recipient_email(
        recipient_email or out.get("to_email") or out.get("recipient_email")
    )
    out["deliverability"] = {
        "quality": quality,
        "recipient_email": recipient_check,
        "send_window": send_hint,
        "follow_up": follow_up_schedule(send_hint["suggested_send_at_utc"]),
        "editor_notes": [
            "首封：一个具体问题 + 一个规格点 + 一个低压力 CTA（回复规格/目的港）",
            "勿用促销腔、多链接、全大写主题",
            f"建议在买家本地 {send_hint['local_window']} 发送",
        ],
    }
    return out


def pack_deliverability_summary(letters: list[dict[str, Any]]) -> dict[str, Any]:
    """pack_deliverability_summary。

    参数说明：
    :param letters: 参数 letters
    :return: 返回处理结果。
    """
    scores = [
        (L.get("deliverability") or {}).get("quality", {}).get("score", 0) for L in letters
    ]
    avg = round(sum(scores) / len(scores), 1) if scores else 0
    ready = sum(
        1
        for L in letters
        if ((L.get("deliverability") or {}).get("quality") or {}).get("send_ready")
    )
    return {
        "average_quality_score": avg,
        "send_ready_count": ready,
        "total": len(letters),
        "human_review_required": ready < len(letters),
        "checklist": deliverability_checklist(),
        "policy": "开发信仅草稿；score≥70 且 spam 风险≤1 可标「待发送」；真发仍须 SPF/DKIM 与人工确认",
    }
