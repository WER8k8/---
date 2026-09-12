"""
Trade AI Assistant — OSINT 编排器：完整尽职调查流程。

osint_full_check() 是 OSINT 模块的统一入口，接收邮箱/域名/公司名，
自动识别类型后依次执行 6 层检测，最终输出综合风险评分报告。
"""

from __future__ import annotations

import asyncio
import re

from app.services.foreign_trade.osint.email_verify import verify_corporate_email
from app.services.foreign_trade.osint.linkedin_verify import linkedin_company_verify
from app.services.foreign_trade.osint.sanctions import check_sanctions
from app.services.foreign_trade.osint.scoring import compute_risk_score, generate_recommendations
from app.services.foreign_trade.osint.tech_stack import detect_tech_stack
from app.services.foreign_trade.osint.whois import domain_whois


async def _osint_full_check_extracted():
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param self: 输入参数
    :return: 返回 report 等计算结果
    """
    """完整 OSINT 尽职调查（异步编排，LLM 友好）。

    接收邮箱 / 域名 / 公司名，自动识别类型，依次执行各层检测，
    最终输出综合风险评分报告。

    Args:
        target: 邮箱 / 域名 / 公司名（自动识别）
        include_sanctions: 是否包含制裁名单筛查（默认 True）
        include_tech_stack: 是否包含技术栈检测（默认 True）
        include_linkedin: 是否包含 LinkedIn 验证（默认 True）

    Returns:
        完整报告 dict，结构见需求文档 3.11.8 节：
        {
            "target": str,
            "target_type": str,       # "email" | "domain" | "url" | "company"
            "overall_rating": str,    # "low" | "medium" | "high" | "unknown"
            "overall_score": int,     # 0-100
            "flags": list[str],       # 红旗标记列表
            "layers": {               # 各层检测结果
                "email_registration": dict | None,
                "domain_intel": dict,
                "email_verification": dict | None,
                "tech_stack": dict | None,
                "sanctions": dict | None,
                "linkedin": dict | None,
            },
            "recommendations": list[str],  # 行动建议
        }
    """
    target = target.strip()
    target_type = _detect_target_type(target)
    report = _init_osint_report(target, target_type)
    # ── 确定用于域名查询的目标 ──
    loop = asyncio.get_running_loop()
    domain_from_email = _extract_domain_from_email(target, target_type)
    lookup_domain = _extract_lookup_domain(target, target_type, domain_from_email)
    # ── Layer 1: Email registration (holehe) ─────────────────────────────
    await _layer1_email_registration(report, target_type, target, loop)
    # ── Layer 2: WHOIS 域名查询（放入 executor 避免阻塞事件循环）─────────
    await _layer2_whois(report, lookup_domain, loop)
    # ── Layer 3: 企业邮箱验证 ───────────────────────────────────────────
    await _layer3_email_verification(report, target_type, target, loop)
    # ── Layer 4 (可选): 技术栈检测 ─────────────────────────────────────
    await _layer4_tech_stack(report, include_tech_stack, lookup_domain, loop)
    # ── Layer 5 (可选): 制裁名单筛查 ───────────────────────────────────
    await _layer5_sanctions(report, include_sanctions, domain_from_email, target, loop)
    # ── Layer 6: LinkedIn 验证（生成 browser_navigate 指令）─────────────
    _layer6_linkedin(report, include_linkedin, lookup_domain, target, target_type)
    # ── 综合评分与建议 ───────────────────────────────────────────────────
    _finalize_osint_report(report)
    return report


def _init_osint_report(target: str, target_type: str) -> dict:
    """初始化 OSINT 报告基础结构。"""
    return {
        "target": target,
        "target_type": target_type,
        "overall_rating": "unknown",
        "overall_score": 0,
        "flags": [],
        "layers": {},
        "recommendations": [],
    }


def _extract_domain_from_email(target: str, target_type: str) -> str | None:
    """邮箱目标时从地址提取域名用于后续检测，非邮箱目标返回 None。"""
    if target_type == "email":
        return target.split("@", 1)[1]
    return None


async def _layer1_email_registration(report: dict, target_type: str, target: str, loop) -> None:
    """Layer 1：邮箱注册检测（holehe），非邮箱目标跳过。"""
    if target_type == "email":
        report["layers"]["email_registration"] = await _run_email_check(target)
    else:
        report["layers"]["email_registration"] = None


async def _layer2_whois(report: dict, lookup_domain: str | None, loop) -> None:
    """Layer 2：WHOIS 域名查询，并按域名年龄追加红旗标记。"""
    if lookup_domain:
        whois_result = await loop.run_in_executor(None, domain_whois, lookup_domain)
        report["layers"]["domain_intel"] = whois_result
        if whois_result.get("age_category") == "new":
            report["flags"].append("domain_age_new")
        if whois_result.get("days_old") and whois_result["days_old"] > 3650:
            report["flags"].append("domain_age_old")
    else:
        report["layers"]["domain_intel"] = {
            "skipped": True, "reason": "Company target — domain discovery requires web search first"
        }


async def _layer3_email_verification(report: dict, target_type: str, target: str, loop) -> None:
    """Layer 3：企业邮箱验证，个人邮箱域名时标记风险。"""
    if target_type == "email":
        email_verify_result = await loop.run_in_executor(None, verify_corporate_email, target)
        report["layers"]["email_verification"] = email_verify_result
        if email_verify_result.get("risk_flag"):
            report["flags"].append("personal_email_domain")
    else:
        report["layers"]["email_verification"] = None


async def _layer4_tech_stack(report: dict, include_tech_stack: bool, lookup_domain: str | None, loop) -> None:
    """Layer 4（可选）：技术栈检测，免费建站平台时标记风险。"""
    if include_tech_stack and lookup_domain:
        tech_result = await loop.run_in_executor(None, detect_tech_stack, f"https://{lookup_domain}")
        report["layers"]["tech_stack"] = tech_result
        if tech_result.get("is_free_platform"):
            report["flags"].append("free_platform")
    else:
        report["layers"]["tech_stack"] = None


async def _layer5_sanctions(report: dict, include_sanctions: bool, domain_from_email: str | None, target: str, loop) -> None:
    """Layer 5（可选）：制裁名单筛查，命中时标记严重风险。"""
    if include_sanctions:
        sanctions_name = domain_from_email or target
        sanctions_result = await loop.run_in_executor(None, check_sanctions, sanctions_name)
        report["layers"]["sanctions"] = sanctions_result
        if sanctions_result.get("is_sanctioned"):
            report["flags"].append("sanctioned")
    else:
        report["layers"]["sanctions"] = None


def _layer6_linkedin(report: dict, include_linkedin: bool, lookup_domain: str | None, target: str, target_type: str) -> None:
    """Layer 6：LinkedIn 验证，生成 browser_navigate 指令。"""
    if include_linkedin and lookup_domain:
        _company_hint = target if target_type == "company" else lookup_domain
        report["layers"]["linkedin"] = linkedin_company_verify(lookup_domain, _company_hint)
    else:
        report["layers"]["linkedin"] = None


def _finalize_osint_report(report: dict) -> dict:
    """综合评分、评级并生成行动建议，返回填充完成的报告。"""
    score, rating = compute_risk_score(report["flags"])
    report["overall_score"] = score
    report["overall_rating"] = rating
    report["recommendations"] = generate_recommendations(report)
    return report

async def osint_full_check(
    target: str,
    *,
    include_sanctions: bool = True,
    include_tech_stack: bool = True,
    include_linkedin: bool = True,
) -> dict:
    """osint_full_check。

    参数说明：
    :param target: 参数 target
    :param include_sanctions: 参数 include_sanctions
    :param include_tech_stack: 参数 include_tech_stack
    :param include_linkedin: 参数 include_linkedin
    :return: 返回处理结果。
    """
    report = await _osint_full_check_extracted()
    return report


# ─────────────────────────────────────────────────────────────────────────────
# 内部 helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_lookup_domain(target: str, target_type: str, domain_from_email: str | None) -> str | None:
    """从目标中提取用于 WHOIS / 技术栈检测的域名。

    公司名无法直接提取域名（需先搜索发现官网），返回 None。
    URL 使用 urllib.parse 精确解析，避免路径参数残留。
    """
    if domain_from_email:
        return domain_from_email

    if target_type == "url":
        from urllib.parse import urlparse
        parsed = urlparse(target)
        netloc = parsed.netloc.lower().removeprefix("www.")
        return netloc or None

    if target_type == "domain":
        return target.lower().removeprefix("www.")

    # company / unknown — 无法直接提取域名
    return None


def _detect_target_type(target: str) -> str:
    """自动识别目标类型：email / domain / url / company。

    识别规则：
      - 含 @ → email
      - 含 http(s):// → url
      - 符合域名格式 (含 . 和合法 TLD) → domain
      - 否则 → company
    """
    target = target.strip()
    if "@" in target and "." in target.split("@", 1)[1]:
        # 含 @ 且 @ 后有 . → 视为邮箱地址
        return "email"
    if target.startswith(("http://", "https://")):
        # 以 http(s):// 开头 → 视为 URL
        return "url"
    if re.match(r"^[a-z0-9]([a-z0-9-]+\.)+[a-z]{2,}$", target.lower()):
        # 符合标准域名格式（如 example.com）→ 视为域名
        return "domain"
    # 以上都不匹配 → 视为公司名称
    return "company"


async def _run_email_check(email: str) -> dict:
    """Layer 1：邮箱注册检测（holehe 可选；未安装则跳过）。"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, _email_registration_check_sync, email)
        return result
    except Exception as e:
        return {"error": str(e), "checked_count": 0, "found_count": 0, "skipped": True}


def _email_registration_check_sync(email: str) -> dict:
    """实现 邮件registration检查同步 的功能。
    
    :param email: 参数 email（类型: str）
    :return: 返回 dict 结果
    """
    try:
        import importlib
        holehe = importlib.import_module("holehe")
        # holehe API varies; if unavailable return skip
        return {
            "email": email,
            "skipped": False,
            "note": "holehe optional; install holehe for full layer-1",
            "found_count": 0,
        }
    except ImportError:
        return {
            "email": email,
            "skipped": True,
            "reason": "holehe_not_installed",
            "note": "Layer1 optional — WHOIS/MX/sanctions still run",
        }
