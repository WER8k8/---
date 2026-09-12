"""询盘智能 enrichment — 意向分 + Discovery 追问（列表/详情共用）。"""

from __future__ import annotations

import re
from typing import Any

from app.services.ubrain.inquiry_discovery_service import build_discovery_questions
from app.services.ubrain.inquiry_scoring_service import score_inquiry_lead

_DISCOVERY_BLOCK = re.compile(r"\n---\n【待追问】[\s\S]*$", re.M)
_LEVEL_LABEL = {"high": "高", "medium": "中", "low": "低"}


def strip_discovery_block(message: str | None) -> str:
    """strip_discovery_block。

    参数说明：
    :param message: 参数 message
    :return: 返回处理结果。
    """
    if not message:
        return ""
    return _DISCOVERY_BLOCK.sub("", message).rstrip()


def discovery_questions_for_inquiry(inquiry: dict[str, Any]) -> list[dict[str, str]]:
    """discovery_questions_for_inquiry。

    参数说明：
    :param inquiry: 参数 inquiry
    :return: 返回处理结果。
    """
    raw = inquiry.get("message") or ""
    if "【待追问】" in raw:
        block = raw.split("【待追问】", 1)[-1]
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        parsed: list[dict[str, str]] = []
        for ln in lines:
            m = re.match(r"(\d+)\.\s*(.+)", ln)
            if m:
                parsed.append(
                    {
                        "id": f"q{m.group(1)}",
                        "label": f"追问 {m.group(1)}",
                        "question": m.group(2).strip(),
                    }
                )
        if parsed:
            return parsed
    return build_discovery_questions(
        product=str(inquiry.get("product") or inquiry.get("product_interest") or ""),
        message=strip_discovery_block(raw),
    )


def enrich_inquiry_intel(item: dict[str, Any]) -> dict[str, Any]:
    """enrich_inquiry_intel。

    参数说明：
    :param item: 参数 item
    :return: 返回处理结果。
    """
    scored = score_inquiry_lead("", inquiry=item)
    item["intent_score"] = scored["score"]
    item["intent_level"] = scored["level"]
    item["intent_next_action"] = scored["next_action"]
    item["intent_reasons"] = scored.get("reasons") or []
    item["intent_label"] = f"{_LEVEL_LABEL.get(scored['level'], scored['level'])} ({scored['score']})"
    item["discovery_questions"] = discovery_questions_for_inquiry(item)
    item["message_clean"] = strip_discovery_block(str(item.get("message") or ""))
    return item
