# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GW-G-CC-04 — 发布前人审清单（数字/认证/MOQ）。"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from app.models.content_master import ContentMaster

CHECKLIST_KEYS = (
    "moq_verified",
    "certification_claims_reviewed",
    "numbers_reviewed",
    "human_approved",
)

CERT_PATTERN = re.compile(
    r"\b(ISO\s?\d+|CE\b|UL\b|FDA|RoHS|REACH|SASO|BSCI|SGS|TUV|认证|证书)\b",
    re.I,
)
NUMBER_CLAIM = re.compile(
    r"(\d{2,}(%|\s*(吨|件|套|台|USD|\$|MOQ|days|天|hours|小时)))",
    re.I,
)
MOQ_PATTERN = re.compile(r"\b(MOQ|最小起订|minimum order)\b", re.I)


def load_preflight_checklist(master: ContentMaster | None) -> dict[str, bool]:
    """实现 加载preflightchecklist 的功能。
    
    :param master: 参数 master（类型: ContentMaster | None）
    :return: 返回 dict[str, bool] 结果
    """
    if not master or not master.preflight_checklist_json:
        return {}
    try:
        raw = json.loads(master.preflight_checklist_json)
    except (TypeError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(k): bool(v) for k, v in raw.items()}


def apply_preflight_checklist(
    master: ContentMaster,
    checklist: dict[str, bool] | None,
    *,
    user_id: str | None = None,
) -> None:
    """实现 应用preflightchecklist 的功能。
    
    :param master: 参数 master（类型: ContentMaster）
    :param checklist: 参数 checklist（类型: dict[str, bool] | None）
    :param user_id: 参数 user_id（类型: str | None）
    :return: 返回 None 结果
    """
    if checklist is None:
        return
    master.preflight_checklist_json = json.dumps(checklist, ensure_ascii=False)
    if checklist.get("human_approved"):
        master.preflight_approved_at = datetime.now(timezone.utc)
        if user_id:
            master.preflight_approved_by = user_id


def scan_content_risks(body: str) -> list[dict[str, str]]:
    """实现 扫描内容risks 的功能。
    
    :param body: 参数 body（类型: str）
    :return: 返回 list[dict[str, str]] 结果
    """
    risks: list[dict[str, str]] = []
    text = body or ""
    if CERT_PATTERN.search(text):
        risks.append(
            {
                "code": "certification_claim",
                "message": "内容含认证/证书表述，发布前请确认可公开证明文件。",
            }
        )
    if NUMBER_CLAIM.search(text):
        risks.append(
            {
                "code": "numeric_claim",
                "message": "内容含数量/价格/交期数字，请人工核对是否与报价单一致。",
            }
        )
    if MOQ_PATTERN.search(text) and not re.search(r"\d", text):
        risks.append(
            {
                "code": "moq_without_number",
                "message": "提到 MOQ 但未给出具体数量。",
            }
        )
    return risks


def validate_preflight(
    master: ContentMaster | None,
    checklist: dict[str, bool] | None = None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """实现 校验preflight 的功能。
    
    :param master: 参数 master（类型: ContentMaster | None）
    :param checklist: 参数 checklist（类型: dict[str, bool] | None）
    :param force: 参数 force（类型: bool）
    :return: 返回 dict[str, Any] 结果
    """
    checklist = checklist or {}
    body = (master.body if master else "") or ""
    title = (master.title if master else "") or ""
    risks = scan_content_risks(f"{title}\n{body}")
    missing = [k for k in CHECKLIST_KEYS if not checklist.get(k)]
    blocked = bool(risks and not checklist.get("human_approved"))
    if missing and not force:
        blocked = True

    return {
        "ok": not blocked or force,
        "blocked": blocked and not force,
        "checklist_required": list(CHECKLIST_KEYS),
        "checklist_missing": missing,
        "content_risks": risks,
        "force_allowed": True,
        "gw_task": "GW-G-CC-04",
        "message": (
            "发布已阻断：请完成人审清单并确认认证/数字/MOQ。"
            if blocked and not force
            else "preflight_passed"
        ),
    }


def assert_publish_allowed(
    master: ContentMaster | None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """实现 assert发布allowed 的功能。
    
    :param master: 参数 master（类型: ContentMaster | None）
    :param context: 参数 context（类型: dict[str, Any] | None）
    :return: 返回 dict[str, Any] 结果
    """
    ctx = context or {}
    checklist = ctx.get("preflight_checklist") or {}
    force = bool(ctx.get("preflight_force"))
    result = validate_preflight(master, checklist, force=force)
    if result["blocked"]:
        result["status"] = "blocked"
        result["next_step"] = (
            "在 context 传入 preflight_checklist（moq_verified/certification_claims_reviewed/"
            "numbers_reviewed/human_approved=true）或 preflight_force=true（运维）"
        )
    else:
        result["status"] = "ready"
    return result
